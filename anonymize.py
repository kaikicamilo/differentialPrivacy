import os
import json
import pandas as pd
import numpy as np

# Carrega variáveis de ambiente do .env
from dotenv import load_dotenv
load_dotenv()

# Nova importação: utiliza o cliente OpenAI ao invés do openai.ChatCompletion
from openai import OpenAI

# Instancia o cliente com a sua chave da OpenAI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def carregar_arquivo(file_path="C:/Users/kkaik/OneDrive/Área de Trabalho/pdsi aldo/differentialPrivacy/2023_TAB21_FOLHA_PAGAMENTO.xlsx - DADOS.csv"):
    """Carrega CSV ou Excel de acordo com a extensão."""
    if not os.path.exists(file_path):
        print(f"O arquivo {file_path} não existe. Verifique se o caminho está correto.")
        return None, None

    if file_path.lower().endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    file_name = os.path.basename(file_path)
    print(f"\nArquivo '{file_name}' carregado com sucesso!")
    return df, file_name


def classificar_coluna_com_llm(coluna, exemplos):
    """
    Envia ao LLM (ChatGPT) o nome da coluna + alguns valores de exemplo para classificação.
    Retorna (tipo_coluna, eh_sensivel, explicacao).
    """

    prompt = f"""
Você é um sistema de classificação de dados sensíveis com base na Lei Geral de Proteção de Dados (LGPD) do Brasil.
Receberá o NOME DE UMA COLUNA e ALGUNS VALORES DE EXEMPLO dessa coluna.
Precisamos classificar essa coluna em uma das seguintes categorias:

1) "identificador": ex. nome completo, CPF, CNPJ, telefone, email, RG, passaporte etc.
2) "quase_identificador": ex. CEP, endereço, data de nascimento, data de admissão (qualquer data pessoal), etc.
3) "financeiro": ex. salário, renda, valor monetário, comissão, desconto, imposto, etc.
4) "demografico": ex. idade, número de filhos, gênero, raça, etc.
5) "texto": quando não se enquadrar em nenhum caso sensível acima.

Além disso, precisamos definir se é dado sensível ou não ("eh_sensivel"):
- Se for "identificador", "quase_identificador", "financeiro" ou "demografico", então eh_sensivel = true.
- Caso contrário, eh_sensivel = false, e categorizamos como "texto".

Também precisamos de uma EXPLICAÇÃO que justifique a decisão de acordo com a LGPD, incluindo por que a coluna foi classificada como sensível ou não.
Exemplo de estrutura do JSON de resposta:
{{
  "tipo_coluna": "financeiro",
  "eh_sensivel": true,
  "explicacao": "Este dado refere-se a valores monetários (salário), que de acordo com a LGPD é classificado como dado pessoal sensível."
}}

A resposta **deve** ser estritamente em formato JSON, com as chaves: "tipo_coluna", "eh_sensivel" e "explicacao".

Agora avalie:
NOME DA COLUNA: "{coluna}"
EXEMPLOS (máx 5):
{exemplos}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300
        )
        # Agora o conteúdo vem de response.choices[0].message.content
        content = response.choices[0].message.content

        result = json.loads(content)

        tipo_coluna = result.get("tipo_coluna", "texto").lower()
        eh_sensivel = bool(result.get("eh_sensivel", False))
        explicacao = result.get("explicacao", "Sem explicação provida.")

        return tipo_coluna, eh_sensivel, explicacao

    except Exception as e:
        print(f"[ERRO] Falha ao classificar coluna '{coluna}': {e}")
        return "texto", False, "Não foi possível obter explicação da LLM."


def aplicar_differential_privacy(df, coluna, epsilon=1.0):
    """
    Aplica mecanismo de Laplace para adicionar ruído a dados numéricos sensíveis.
    Quanto menor o epsilon, maior a privacidade (mais ruído).
    """
    sensibilidade = 1
    
    #Cria uma máscara para valores que não sejam 0
    mask = df[coluna] != 0

    #Gera o ruído somente para os valores não-zero
    ruido = np.random.laplace(loc=0, scale=sensibilidade/epsilon, size=mask.sum())

    #Aplica o ruído somente onde o valor era != 0
    df.loc[mask, coluna] = (df.loc[mask, coluna] + ruido).round(2)


def mascarar_quase_identificador(df, coluna):
    """
    Exemplo simples de 'mascarar' colunas com dados que sejam 'quase_identificador'.
    - Se for string (ex. endereço): remover detalhes ou substituir parte por '***'.
    - Se for data (ex. data de nascimento): substituir dia por '01' ou suprimir dia.
    """
    if pd.api.types.is_datetime64_any_dtype(df[coluna]):
        # Exemplo: manter apenas mês/ano, trocar dia para 1
        df[coluna] = df[coluna].apply(lambda d: d.replace(day=1) if not pd.isna(d) else d)
    else:
        # Se for string: por exemplo, manter só as primeiras 5 letras + '***'
        df[coluna] = df[coluna].astype(str).apply(lambda x: x[:5] + "***" if len(x) > 5 else x + "***")


def anonimizar_planilha(file_path, output_path=None):
    """
    Lê o arquivo de entrada (CSV ou Excel), classifica cada coluna com o LLM,
    aplica a anonimização apropriada e salva o resultado em 'output_path' ou
    em "<nome_original>_anonimizado.xlsx" caso 'output_path' seja None.
    """
    df, file_name = carregar_arquivo(file_path)
    if df is None:
        print("Não foi possível carregar o arquivo. Verifique o caminho.")
        return

    df_anonimizado = df.copy()
    colunas = df_anonimizado.columns

    for coluna in colunas:
        valores_unicos = df_anonimizado[coluna].dropna().unique()
        if len(valores_unicos) == 0:
            print(f"[INFO] Coluna '{coluna}' vazia ou só NaN. Pulando classificação.")
            continue

        exemplos_selecionados = pd.Series(valores_unicos).sample(min(10, len(valores_unicos)), random_state=42)
        exemplos_str = "\n".join(str(x) for x in exemplos_selecionados)

        tipo_coluna, eh_sensivel, explicacao = classificar_coluna_com_llm(coluna, exemplos_str)

        # Imprime a explicação antes de tomar a ação
        print(f"\n[CLASSIFICAÇÃO] Coluna '{coluna}':")
        print(f"Tipo: {tipo_coluna}, eh_sensivel: {eh_sensivel}")
        print(f"Explicação (baseada na LGPD): {explicacao}")

        if eh_sensivel:
            if tipo_coluna == "identificador":
                # Removemos a coluna
                df_anonimizado.drop(columns=[coluna], inplace=True)
                print(f"[DROP] Coluna '{coluna}' => tipo '{tipo_coluna}'. Removida com base na LGPD.")
            elif tipo_coluna in ["financeiro", "demografico"]:
                # Se for numérico, aplicar DP; se não for numérico, removemos
                if pd.api.types.is_numeric_dtype(df_anonimizado[coluna]):
                    aplicar_differential_privacy(df_anonimizado, coluna, epsilon=1.0)
                    print(f"[DP] Coluna '{coluna}' => tipo '{tipo_coluna}'. Privacidade diferencial aplicada.")
                else:
                    df_anonimizado.drop(columns=[coluna], inplace=True)
                    print(f"[DROP] Coluna '{coluna}' não é numérica mas foi classificada como '{tipo_coluna}'. Removida.")
            elif tipo_coluna == "quase_identificador":
                df_anonimizado[coluna] = pd.to_datetime(df_anonimizado[coluna], errors="coerce")
                mascarar_quase_identificador(df_anonimizado, coluna)
                print(f"[MASK] Coluna '{coluna}' => tipo '{tipo_coluna}'. Aplicado mascaramento.")
            else:
                # qualquer outra sensível => dropar
                df_anonimizado.drop(columns=[coluna], inplace=True)
                print(f"[DROP] Coluna '{coluna}' => tipo '{tipo_coluna}'. Removida.")
        else:
            # Se não for sensível, mantemos a coluna como está
            print(f"[OK] Coluna '{coluna}' => tipo '{tipo_coluna}', não sensível. Mantida.")

    # Se não foi definido um output_path, gera um automaticamente
    if not output_path:
        base_name, _ = os.path.splitext(file_name)
        output_path = f"{base_name}_anonimizado.xlsx"

    df_anonimizado.to_excel(output_path, index=False)
    print(f"\n[SUCESSO] Planilha anonimizada salva como '{output_path}'.")
    print("Download concluído (em ambiente local, o arquivo está na mesma pasta do script).")


if __name__ == "__main__":
    anonimizar_planilha()