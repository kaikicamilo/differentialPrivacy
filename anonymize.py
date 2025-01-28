########################################
# Configuração Inicial
# - Importa bibliotecas essenciais como pandas, numpy e dotenv.
# - Carrega as variáveis de ambiente do arquivo .env (contendo a chave da API OpenAI).
# - Instancia o cliente OpenAI para classificar dados sensíveis.
########################################

import os
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

########################################
# Função: carregar_arquivo
# - Lê um arquivo CSV ou Excel enviado pelo usuário.
# - Verifica se o arquivo existe antes de carregá-lo.
# - Retorna um DataFrame com os dados e o nome do arquivo.
########################################

def carregar_arquivo(file_path):
    """Carrega CSV ou Excel de acordo com a extensão enviada pelo usuário."""
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

########################################
# Função: classificar_coluna_com_llm
# - Envia o nome da coluna e alguns valores de exemplo para a API OpenAI.
# - Retorna a classificação do tipo de dado (identificador, financeiro, etc.).
# - Também retorna se o dado é sensível e uma explicação baseada na LGPD.
########################################

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
        content = response.choices[0].message.content

        result = json.loads(content)

        tipo_coluna = result.get("tipo_coluna", "texto").lower()
        eh_sensivel = bool(result.get("eh_sensivel", False))
        explicacao = result.get("explicacao", "Sem explicação provida.")

        return tipo_coluna, eh_sensivel, explicacao

    except Exception as e:
        print(f"[ERRO] Falha ao classificar coluna '{coluna}': {e}")
        return "texto", False, "Não foi possível obter explicação da LLM."

########################################
# Função: aplicar_differential_privacy
# - Aplica o mecanismo de Laplace para adicionar ruído a dados sensíveis.
# - Ignora valores iguais a zero para evitar distorções desnecessárias.
# - O nível de ruído é controlado pelo parâmetro "epsilon".
########################################

def aplicar_differential_privacy(df, coluna, epsilon=1.0):
    """
    Aplica mecanismo de Laplace para adicionar ruído a dados numéricos sensíveis.
    Quanto menor o epsilon, maior a privacidade (mais ruído).
    """
    sensibilidade = 1
    
    #Cria uma máscara para valores que não sejam 0
    mask = df[coluna] != 0

    ruido = np.random.laplace(loc=0, scale=sensibilidade/epsilon, size=mask.sum())

    df.loc[mask, coluna] = (df.loc[mask, coluna] + ruido).round(2)

########################################
# Função: mascarar_quase_identificador
# - Mascaramento simples para dados classificados como quase-identificadores.
# - Ajusta datas para o primeiro dia do mês.
# - Trunca textos, mantendo apenas os primeiros 5 caracteres e adicionando "***".
########################################

def mascarar_quase_identificador(df, coluna):
    """
    Exemplo simples de 'mascarar' colunas com dados que sejam 'quase_identificador'.
    - Se for string (ex. endereço): remover detalhes ou substituir parte por '***'.
    - Se for data (ex. data de nascimento): substituir dia por '01' ou suprimir dia.
    """
    if pd.api.types.is_datetime64_any_dtype(df[coluna]):
        #Exemplo: manter apenas mês/ano, trocar dia para 1
        df[coluna] = df[coluna].apply(lambda d: d.replace(day=1) if not pd.isna(d) else d)
    else:
        #Se for string: por exemplo, manter só as primeiras 5 letras + '***'
        df[coluna] = df[coluna].astype(str).apply(lambda x: x[:5] + "***" if len(x) > 5 else x + "***")

########################################
# Função: anonimizar_planilha
# - Processo principal de anonimização:
#   1. Carrega o arquivo enviado.
#   2. Classifica cada coluna usando o LLM.
#   3. Remove identificadores e mascara quase-identificadores.
#   4. Identifica colunas financeiras/demográficas para aplicação futura de DP.
# - Salva um arquivo intermediário, sem privacidade diferencial aplicada.
# - Retorna as colunas marcadas para DP e o caminho do arquivo intermediário.
########################################

def anonimizar_planilha(file_path, output_path=None):
    """
    Lê o arquivo de entrada (CSV ou Excel), classifica cada coluna com o LLM,
    aplica remoção/mascaramento adequado conforme a LGPD, e salva um arquivo
    intermediário (sem DP) em 'output_path' ou em "<nome_original>_anonimizado.xlsx"
    se 'output_path' for None.

    Retorna:
      - dp_columns: lista de colunas classificadas como 'financeiro' ou 'demografico'
        e que podem receber DP no passo seguinte.
      - output_path: caminho do arquivo Excel gerado (sem ruído laplaciano).
    """
    df, file_name = carregar_arquivo(file_path)
    if df is None:
        print("Não foi possível carregar o arquivo. Verifique o caminho.")
        return [], None

    df_anonimizado = df.copy()
    colunas = df_anonimizado.columns

    #Lista para guardar colunas em que DP pode ser aplicada (financeiro/demografico numérico)
    dp_columns = []

    for coluna in colunas:
        valores_unicos = df_anonimizado[coluna].dropna().unique()
        if len(valores_unicos) == 0:
            print(f"[INFO] Coluna '{coluna}' vazia ou só NaN. Pulando classificação.")
            continue

        exemplos_selecionados = pd.Series(valores_unicos).sample(min(10, len(valores_unicos)), random_state=42)
        exemplos_str = "\n".join(str(x) for x in exemplos_selecionados)

        tipo_coluna, eh_sensivel, explicacao = classificar_coluna_com_llm(coluna, exemplos_str)

        #Imprime a explicação antes de tomar a ação
        print(f"\n[CLASSIFICAÇÃO] Coluna '{coluna}':")
        print(f"Tipo: {tipo_coluna}, eh_sensivel: {eh_sensivel}")
        print(f"Explicação (baseada na LGPD): {explicacao}")

        if eh_sensivel:
            if tipo_coluna == "identificador":
                #Remove colunas identificadoras
                df_anonimizado.drop(columns=[coluna], inplace=True)
                print(f"[DROP] Coluna '{coluna}' => tipo '{tipo_coluna}'. Removida com base na LGPD.")

            elif tipo_coluna in ["financeiro", "demografico"]:
                #Se for numérico, poderemos aplicar DP depois
                if pd.api.types.is_numeric_dtype(df_anonimizado[coluna]):
                    dp_columns.append(coluna)
                    print(f"[DEFER] Coluna '{coluna}' => tipo '{tipo_coluna}'. Marcada para DP futura.")
                else:
                    df_anonimizado.drop(columns=[coluna], inplace=True)
                    print(f"[DROP] Coluna '{coluna}' não é numérica mas foi classificada como '{tipo_coluna}'. Removida.")

            elif tipo_coluna == "quase_identificador":
                #Converte (possivelmente) para datetime e faz mascaramento
                df_anonimizado[coluna] = pd.to_datetime(df_anonimizado[coluna], errors="coerce")
                mascarar_quase_identificador(df_anonimizado, coluna)
                print(f"[MASK] Coluna '{coluna}' => tipo '{tipo_coluna}'. Aplicado mascaramento.")

            else:
                #Qualquer outra sensível => dropar
                df_anonimizado.drop(columns=[coluna], inplace=True)
                print(f"[DROP] Coluna '{coluna}' => tipo '{tipo_coluna}'. Removida.")

        else:
            #Se não for sensível, mantemos a coluna como está
            print(f"[OK] Coluna '{coluna}' => tipo '{tipo_coluna}', não sensível. Mantida.")

    if not output_path:
        base_name, _ = os.path.splitext(file_name)
        output_path = f"{base_name}_anonimizado.xlsx"

    df_anonimizado.to_excel(output_path, index=False)
    print(f"\n[SUCESSO] Planilha anonimizada salva como '{output_path}'.")
    print("Download concluído (em ambiente local, o arquivo está na mesma pasta do script).")

    return dp_columns, output_path

########################################
# Função: aplicar_dp_pos_classificacao
# - Recebe o arquivo intermediário e uma lista de colunas classificadas como sensíveis.
# - Aplica ruído Laplace (privacidade diferencial) apenas nas colunas numéricas relevantes.
# - Salva e retorna o caminho do arquivo final anonimizado.
########################################

def aplicar_dp_pos_classificacao(file_path, dp_columns, epsilon=1.0, output_path=None):
    """
    Lê o arquivo 'file_path' (excel intermediário, já anonimizado exceto pela DP),
    aplica ruído Laplace nas colunas listadas em 'dp_columns'
    e salva no 'output_path' (ou <file_path>_dp.xlsx se não especificado).
    
    Retorna o caminho do arquivo final.
    """
    if not os.path.exists(file_path):
        print(f"[ERRO] Arquivo intermediário '{file_path}' não encontrado.")
        return None

    df = pd.read_excel(file_path)

    for coluna in dp_columns:
        if coluna in df.columns:
            aplicar_differential_privacy(df, coluna, epsilon=epsilon)
            print(f"[DP] Coluna '{coluna}' - epsilon={epsilon}")

    if not output_path:
        base, ext = os.path.splitext(file_path)
        output_path = base + "_dp.xlsx"

    df.to_excel(output_path, index=False)
    print(f"[SUCESSO] DP aplicada e salvo em '{output_path}'")
    return output_path


if __name__ == "__main__":
    anonimizar_planilha()