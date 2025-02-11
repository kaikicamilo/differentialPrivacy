import os
import json
import logging
import multiprocessing
from typing import Tuple, List, Optional, Union
import pandas as pd
import numpy as np

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Instancia o cliente OpenAI
try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("A chave da API OpenAI não foi encontrada no .env.")
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    logger.error(f"Falha ao configurar OpenAI: {e}")
    raise

def carregar_arquivo(file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Carrega um arquivo CSV ou Excel de acordo com sua extensão.
    Retorna (DataFrame, nome_do_arquivo) ou (None, None) caso o arquivo não exista.
    """
    if not os.path.exists(file_path):
        logger.error(f"O arquivo {file_path} não existe.")
        return None, None

    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"Falha ao ler o arquivo {file_path}: {e}")
        return None, None

    file_name = os.path.basename(file_path)
    logger.info(f"Arquivo '{file_name}' carregado com sucesso.")
    return df, file_name

def _classificar_coluna_api(coluna: str, exemplos_str: str) -> dict:
    """
    Chama a API da OpenAI para classificar uma única coluna.
    Retorna um dicionário com as chaves: tipo_coluna, eh_sensivel, explicacao.
    Em caso de erro, retorna defaults ("texto", False, "Falha...").
    """
    prompt = f"""
Você é um sistema de classificação de dados sensíveis com base na Lei Geral de Proteção de Dados (LGPD) do Brasil e GDPR.
Receberá o NOME DE UMA COLUNA e ALGUNS VALORES DE EXEMPLO dessa coluna.
Precisamos classificar essa coluna em uma das seguintes categorias:

1) "identificador": ex. nome completo, CPF, CNPJ, telefone, email, RG, passaporte etc.
2) "quase_identificador": ex. CEP, endereço, data de nascimento, data de admissão (qualquer data pessoal), etc.
3) "financeiro": ex. salário, renda, valor monetário, comissão, desconto, imposto, etc.
4) "demografico": ex. idade, número de filhos, gênero, raça, etc.
5) "saude": ex. dados de saúde, prontuário, condições médicas, exames etc.
6) "religiao": ex. afiliação religiosa, denominação, etc.
7) "politica": ex. filiação partidária, preferências políticas, etc.
8) "texto": quando não se enquadrar em nenhum caso sensível acima.

Além disso, precisamos definir se é dado sensível ou não ("eh_sensivel"):
- Se for "identificador", "quase_identificador", "financeiro", "demografico", "saude", "religiao", "politica", então eh_sensivel = true.
- Caso contrário, eh_sensivel = false, e categorizamos como "texto".

Também precisamos de uma EXPLICAÇÃO que justifique a decisão de acordo com a LGPD/GDPR, incluindo por que a coluna foi classificada como sensível ou não.
Exemplo de estrutura do JSON de resposta:
{{
  "tipo_coluna": "financeiro",
  "eh_sensivel": true,
  "explicacao": "Este dado refere-se a valores monetários (salário), considerado sensível pela LGPD/GDPR."
}}

A resposta deve ser estritamente em formato JSON com as chaves: "tipo_coluna", "eh_sensivel" e "explicacao".

Agora avalie:
NOME DA COLUNA: "{coluna}"
EXEMPLOS (máx 5):
{exemplos_str}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)

        tipo = result.get("tipo_coluna", "texto").lower()
        sensivel = bool(result.get("eh_sensivel", False))
        explicacao = result.get("explicacao", "Sem explicação provida.")
        return {
            "tipo_coluna": tipo,
            "eh_sensivel": sensivel,
            "explicacao": explicacao
        }
    except Exception as e:
        logger.warning(f"Falha ao classificar coluna '{coluna}': {e}")
        return {
            "tipo_coluna": "texto",
            "eh_sensivel": False,
            "explicacao": "Não foi possível obter explicação da LLM."
        }

def classificar_coluna_com_llm(coluna: str, exemplos: pd.Series) -> Tuple[str, bool, str]:
    """
    Cria o prompt de exemplos e chama a API para classificar a coluna.
    Retorna (tipo_coluna, eh_sensivel, explicacao).
    """
    exemplos_str = "\n".join(str(x) for x in exemplos)
    resultado = _classificar_coluna_api(coluna, exemplos_str)
    return (
        resultado["tipo_coluna"],
        resultado["eh_sensivel"],
        resultado["explicacao"]
    )

def aplicar_differential_privacy(
    df: pd.DataFrame,
    coluna: str,
    epsilon: float = 1.0,
    advanced_technique: bool = False
) -> None:
    """
    Aplica mecanismo de Laplace para adicionar ruído a dados numéricos sensíveis.
    Quanto menor o epsilon, maior a privacidade (mais ruído).
    Se advanced_technique=True, poderíamos usar outra distribuição (ex.: Gaussian) no futuro.
    """
    # Exemplo simples de Laplace
    sensibilidade = 1.0
    mask = (df[coluna] != 0) & (~df[coluna].isna())

    # Caso queira explorar outra distribuição, verifique advanced_technique
    if advanced_technique:
        # Placeholder: Gaussian noise ou outro
        scale = sensibilidade / epsilon
        ruido = np.random.normal(loc=0, scale=scale, size=mask.sum())
    else:
        scale = sensibilidade / epsilon
        ruido = np.random.laplace(loc=0, scale=scale, size=mask.sum())

    df.loc[mask, coluna] = (df.loc[mask, coluna] + ruido).round(2)

def mascarar_quase_identificador(df: pd.DataFrame, coluna: str) -> None:
    """
    Exemplo simples de 'mascarar' colunas com dados que sejam 'quase_identificador'.
    - Se for string (ex. endereço): remover detalhes ou substituir parte por '***'.
    - Se for data (ex. data de nascimento): substituir dia por '01' ou suprimir dia.
    """
    if pd.api.types.is_datetime64_any_dtype(df[coluna]):
        df[coluna] = df[coluna].apply(lambda d: d.replace(day=1) if pd.notna(d) else d)
    else:
        df[coluna] = df[coluna].astype(str).apply(
            lambda x: x[:5] + "***" if len(x) > 5 else x + "***"
        )

def _classificar_uma_coluna(args) -> Tuple[str, str, bool, str]:
    """
    Função auxiliar para paralelizar a classificação de cada coluna.
    args => (coluna, df_coluna_sample)
    Retorna (coluna, tipo_coluna, eh_sensivel, explicacao).
    """
    coluna, exemplos = args
    tipo, eh_sensivel, explicacao = classificar_coluna_com_llm(coluna, exemplos)
    return (coluna, tipo, eh_sensivel, explicacao)

def anonimizar_planilha(
    file_path: str,
    output_path: Optional[str] = None,
    max_workers: int = 4
) -> Tuple[List[str], Optional[str]]:
    """
    Lê o arquivo de entrada (CSV ou Excel), classifica cada coluna com o LLM,
    aplica remoção/mascaramento adequado conforme a LGPD/GDPR, e salva um arquivo
    intermediário (sem DP) em 'output_path' ou em "<nome_original>_anonimizado.xlsx"
    se 'output_path' for None.

    Retorna:
      - dp_columns: lista de colunas classificadas como sensíveis (financeiro, demografico, etc.) e numéricas.
      - output_path: caminho do arquivo Excel gerado (sem ruído laplaciano).
    """
    df, file_name = carregar_arquivo(file_path)
    if df is None:
        logger.error("Falha ao carregar o arquivo. Processo de anonimização abortado.")
        return [], None

    df_anonimizado = df.copy()
    colunas = df_anonimizado.columns.tolist()
    dp_columns: List[str] = []

    # Prepara amostras para todas as colunas
    colunas_com_exemplos = []
    for coluna in colunas:
        col_sem_nulos = df_anonimizado[coluna].dropna()
        if col_sem_nulos.empty:
            logger.info(f"[INFO] Coluna '{coluna}' vazia ou só NaN. Pulando classificação.")
            continue
        exemplos_selecionados = col_sem_nulos.sample(min(10, len(col_sem_nulos)), random_state=42)
        colunas_com_exemplos.append((coluna, exemplos_selecionados))

    # Paraleliza a classificação de colunas para ganhar desempenho
    with multiprocessing.Pool(processes=max_workers) as pool:
        resultados = pool.map(_classificar_uma_coluna, colunas_com_exemplos)

    # Trata os resultados de classificação
    for coluna, tipo_coluna, eh_sensivel, explicacao in resultados:
        logger.info(f"[CLASSIFICAÇÃO] Coluna '{coluna}': tipo={tipo_coluna}, sensível={eh_sensivel}")
        logger.info(f"Explicação: {explicacao}")

        if eh_sensivel:
            if tipo_coluna == "identificador":
                # Remove colunas identificadoras
                df_anonimizado.drop(columns=[coluna], inplace=True)
                logger.info(f"[DROP] Coluna '{coluna}' => tipo '{tipo_coluna}'. Removida.")

            elif tipo_coluna in ["financeiro", "demografico", "saude", "religiao", "politica"]:
                # Se for numérico, poderemos aplicar DP depois
                if pd.api.types.is_numeric_dtype(df_anonimizado[coluna]):
                    dp_columns.append(coluna)
                    logger.info(f"[DEFER] Coluna '{coluna}' => tipo '{tipo_coluna}'. Marcada para DP futura.")
                else:
                    df_anonimizado.drop(columns=[coluna], inplace=True)
                    logger.info(f"[DROP] Coluna '{coluna}' não é numérica mas foi classificada como '{tipo_coluna}'. Removida.")

            elif tipo_coluna == "quase_identificador":
                df_anonimizado[coluna] = pd.to_datetime(df_anonimizado[coluna], errors="coerce")
                mascarar_quase_identificador(df_anonimizado, coluna)
                logger.info(f"[MASK] Coluna '{coluna}' => tipo '{tipo_coluna}'. Aplicado mascaramento.")

            else:
                # Qualquer outra sensível => dropar
                df_anonimizado.drop(columns=[coluna], inplace=True)
                logger.info(f"[DROP] Coluna '{coluna}' => tipo '{tipo_coluna}'. Removida.")
        else:
            logger.info(f"[OK] Coluna '{coluna}' => não sensível. Mantida.")

    if not output_path:
        base_name, _ = os.path.splitext(file_name)
        output_path = f"{base_name}_anonimizado.xlsx"

    try:
        df_anonimizado.to_excel(output_path, index=False)
        logger.info(f"[SUCESSO] Planilha anonimizada salva em '{output_path}'.")
    except Exception as e:
        logger.error(f"Falha ao salvar o arquivo {output_path}: {e}")
        return dp_columns, None

    return dp_columns, output_path

def aplicar_dp_pos_classificacao(
    file_path: str,
    dp_columns: List[str],
    epsilon: float = 1.0,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Lê o arquivo 'file_path' (excel intermediário, já anonimizado exceto pela DP),
    aplica ruído Laplace nas colunas listadas em 'dp_columns'
    e salva no 'output_path' (ou <file_path>_dp.xlsx se não especificado).

    Retorna o caminho do arquivo final ou None em caso de falha.
    """
    if not os.path.exists(file_path):
        logger.error(f"[ERRO] Arquivo intermediário '{file_path}' não encontrado.")
        return None

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"Falha ao ler o arquivo intermediário {file_path}: {e}")
        return None

    for coluna in dp_columns:
        if coluna in df.columns:
            aplicar_differential_privacy(df, coluna, epsilon=epsilon)
            logger.info(f"[DP] Coluna '{coluna}' => epsilon={epsilon}")
        else:
            logger.warning(f"Coluna '{coluna}' não encontrada no arquivo intermediário.")

    if not output_path:
        base, ext = os.path.splitext(file_path)
        output_path = base + "_dp.xlsx"

    try:
        df.to_excel(output_path, index=False)
        logger.info(f"[SUCESSO] DP aplicada e salvo em '{output_path}'")
        return output_path
    except Exception as e:
        logger.error(f"Falha ao salvar o arquivo final {output_path}: {e}")
        return None

# Se quiser rodar diretamente, sem o webservice:
if __name__ == "__main__":
    # Exemplo de uso local
    dp_cols, out_path = anonimizar_planilha("exemplo.csv")
    if dp_cols and out_path:
        aplicar_dp_pos_classificacao(out_path, dp_cols, epsilon=1.0)