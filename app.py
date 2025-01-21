import os
import json
import random
import numpy as np
import pandas as pd
from flask import Flask, request, render_template_string, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from openai import OpenAI
from dotenv import load_dotenv

# --------- CONFIGURAÇÕES GERAIS ---------
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULT_FOLDER"] = RESULT_FOLDER

# Garante que as pastas existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# --------- HTML - TELA INICIAL COM BOOTSTRAP ---------
HTML_INDEX = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>Anonimizador de Planilhas</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
      <span class="navbar-brand">Anonimizador de Planilhas</span>
    </div>
  </nav>

  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-12 col-md-8 col-lg-6">
        <div class="card shadow-sm">
          <div class="card-body">
            <h5 class="card-title text-center mb-4">Selecione seu arquivo</h5>
            <form method="POST" action="/upload" enctype="multipart/form-data">
              <div class="mb-3">
                <label for="fileInput" class="form-label">Upload de arquivo (.xlsx ou .csv)</label>
                <input class="form-control" type="file" name="file" id="fileInput" required>
              </div>
              <div class="d-grid">
                <button type="submit" class="btn btn-primary">Anonimizar</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# --------- FUNÇÕES PRINCIPAIS ---------

def carregar_arquivo(file_path):
    """Carrega CSV ou Excel de acordo com a extensão."""
    if not os.path.exists(file_path):
        print(f"O arquivo {file_path} não existe. Verifique o caminho.")
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
    Envia ao LLM o nome da coluna + alguns valores de exemplo para classificação.
    Retorna (tipo_coluna, eh_sensivel).
    """
    prompt = f"""
Você é um sistema de classificação de dados sensíveis.
Receberá o nome de uma coluna e alguns valores de exemplo.
Com base nas regras abaixo, determine:

- "tipo_coluna"
- "eh_sensivel"

Categorias possíveis:
1) "identificador": ex. nome completo, CPF, telefone, email etc.
2) "quase_identificador": CEP, endereço, datas pessoais etc.
3) "financeiro": salários, valores monetários.
4) "demografico": idade, número de filhos etc.
5) "texto": outros não sensíveis.

Responda no formato JSON:
{{"tipo_coluna": "...", "eh_sensivel": ...}}

Agora avalie:
NOME DA COLUNA: "{coluna}"
EXEMPLOS:
{exemplos}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=100
        )
        result = json.loads(response.choices[0].message.content)
        tipo_coluna = result.get("tipo_coluna", "texto").lower()
        eh_sensivel = bool(result.get("eh_sensivel", False))
        return tipo_coluna, eh_sensivel

    except Exception as e:
        print(f"[ERRO] Classificação da coluna '{coluna}': {e}")
        return "texto", False


def aplicar_differential_privacy(df, coluna, epsilon=1.0):
    """Aplica mecanismo de Laplace para dados numéricos sensíveis."""
    sensibilidade = 1
    ruido = np.random.laplace(loc=0, scale=sensibilidade / epsilon, size=df[coluna].shape)
    df[coluna] = (df[coluna] + ruido).round(2)


def mascarar_quase_identificador(df, coluna):
    """Mascaramento para colunas 'quase_identificador'."""
    if pd.api.types.is_datetime64_any_dtype(df[coluna]):
        df[coluna] = df[coluna].apply(lambda d: d.replace(day=1) if not pd.isna(d) else d)
    else:
        df[coluna] = df[coluna].astype(str).apply(lambda x: x[:5] + "***" if len(x) > 5 else x + "***")


def anonimizar_planilha(file_path):
    """Processa o arquivo e salva no diretório de resultados."""
    df, file_name = carregar_arquivo(file_path)
    if df is None:
        return None

    df_anonimizado = df.copy()

    for coluna in df_anonimizado.columns:
        valores_unicos = df_anonimizado[coluna].dropna().unique()
        if len(valores_unicos) == 0:
            continue

        exemplos_str = "\n".join(str(x) for x in valores_unicos[:5])
        tipo_coluna, eh_sensivel = classificar_coluna_com_llm(coluna, exemplos_str)

        if eh_sensivel:
            if tipo_coluna == "identificador":
                df_anonimizado.drop(columns=[coluna], inplace=True)
            elif tipo_coluna in ["financeiro", "demografico"]:
                if pd.api.types.is_numeric_dtype(df[coluna]):
                    aplicar_differential_privacy(df_anonimizado, coluna)
                else:
                    df_anonimizado.drop(columns=[coluna], inplace=True)
            elif tipo_coluna == "quase_identificador":
                mascarar_quase_identificador(df_anonimizado, coluna)
            else:
                df_anonimizado.drop(columns=[coluna], inplace=True)
        else:
            print(f"[OK] Coluna '{coluna}' mantida.")

    output_file_name = f"{os.path.splitext(file_name)[0]}_anonimizado.xlsx"
    output_path = os.path.join(app.config["RESULT_FOLDER"], output_file_name)
    df_anonimizado.to_excel(output_path, index=False)
    return output_path


# --------- ROTAS FLASK ---------

@app.route("/", methods=["GET"])
def index():
    """Página inicial."""
    return render_template_string(HTML_INDEX)


@app.route("/upload", methods=["POST"])
def upload_file():
    """Recebe o arquivo, processa e retorna o link para download."""
    if "file" not in request.files:
        return "Nenhum arquivo enviado.", 400

    file = request.files["file"]
    if not file.filename:
        return "Arquivo sem nome.", 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(input_path)

    result_path = anonimizar_planilha(input_path)
    if not result_path:
        return "Erro no processamento.", 500

    return redirect(url_for("download_file", result_file=os.path.basename(result_path)))


@app.route("/download/<path:result_file>", methods=["GET"])
def download_file(result_file):
    """Permite baixar o arquivo anonimizado."""
    result_path = os.path.join(app.config["RESULT_FOLDER"], result_file)
    if not os.path.exists(result_path):
        return "Arquivo não encontrado.", 404

    return send_file(result_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)