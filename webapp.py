import os
import tempfile

import gradio as gr
from dotenv import load_dotenv

# Importa as funções do seu anonymize.py
from anonymize import (
    anonimizar_planilha,
    aplicar_dp_pos_classificacao
)

load_dotenv()

########################################
# Passo 1: classificar e gerar arquivo intermediário
########################################
def classify_and_mask(uploaded_file):
    """
    Recebe o arquivo do usuário e chama `anonimizar_planilha`, que:
      - remove/mascara colunas sensíveis,
      - retorna lista de colunas (dp_columns) que podem receber DP (financeiro/demográfico),
      - salva o arquivo intermediário (sem DP).
    """
    if not uploaded_file:
        return None, None, None

    input_path = uploaded_file.name

    # Diretório temporário para armazenar o arquivo intermediário
    tmpdir = tempfile.mkdtemp()
    output_path = os.path.join(tmpdir, "intermediario.xlsx")

    dp_cols, saved_file = anonimizar_planilha(file_path=input_path, output_path=output_path)

    if dp_cols is None or saved_file is None:
        return "Erro ao processar arquivo.", None, None

    if len(dp_cols) == 0:
        # Não há colunas finance/demografico para DP
        msg = "Não há colunas classificadas como financeiro/demográfico."
    else:
        msg = (
            f"Colunas classificadas como financeiro/demográfico:\n"
            f"{', '.join(dp_cols)}"
        )

    return msg, saved_file, ",".join(dp_cols)


########################################
# Passo 2: aplicar DP (opcional)
########################################
def apply_dp(intermediate_file, dp_cols_str, custom_flag, epsilon_value):
    """
    Recebe:
      - intermediate_file: caminho do xlsx intermediário (sem DP) retornado no passo 1
      - dp_cols_str: string com nomes das colunas separados por vírgula
      - custom_flag: "Sim" ou "Não" (usuário escolhe se quer customizar epsilon)
      - epsilon_value: valor de epsilon digitado pelo usuário (float)
    Retorna:
      - Mensagem de status
      - Caminho do arquivo final para download
    """
    if not intermediate_file:
        return "Nenhum arquivo intermediário para processar.", None

    # Se não há colunas dp
    if not dp_cols_str:
        return "Nenhuma coluna DP-eligível detectada.", intermediate_file

    dp_columns = [c.strip() for c in dp_cols_str.split(",") if c.strip()]
    if len(dp_columns) == 0:
        return "Nenhuma coluna DP-eligível detectada (lista vazia).", intermediate_file

    # Define epsilon
    if custom_flag == "Sim":
        try:
            epsilon = float(epsilon_value)
        except:
            epsilon = 1.0
    else:
        epsilon = 1.0

    # Aplica DP
    tmpdir = tempfile.mkdtemp()
    final_path = os.path.join(tmpdir, "anonimizado_final.xlsx")

    result_file = aplicar_dp_pos_classificacao(
        file_path=intermediate_file,
        dp_columns=dp_columns,
        epsilon=epsilon,
        output_path=final_path
    )

    if result_file:
        return f"DP aplicada com epsilon={epsilon}.", result_file
    else:
        return "Ocorreu um erro ao aplicar DP.", None


########################################
# CSS Customizado
########################################
# Ajuste cores, espaçamentos, etc. conforme seu gosto
custom_css = """
/* Corpo da página */
body {
    font-family: 'Inter', sans-serif;
    background: #f2f2f2;
    color: #333;
    margin: 0;
    padding: 0;
}

/* Título principal */
#title {
    text-align: center;
    font-size: 2.2em;
    font-weight: 600;
    color: #3b3b3b;
    margin: 30px 0 10px 0;
}

/* Subtítulo / descrição */
#instructions {
    margin: 0 auto;
    max-width: 650px;
    background-color: #ffffffdd;
    padding: 20px;
    border-radius: 8px;
    line-height: 1.5;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Container dos blocos */
.gr-block, .gr-panel {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 20px;
}

/* Botões */
.gr-button {
    background-color: #0072f5 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 500 !important;
    transition: background-color 0.2s ease;
}
.gr-button:hover {
    background-color: #0056c0 !important;
}

/* File upload: borda e hover */
.gr-file-upload {
    border: 2px dashed #0072f5 !important;
    border-radius: 8px;
}
.gr-file-upload:hover {
    border-color: #0056c0 !important;
}

/* Inputs e Textboxes */
.gr-textbox, .gr-number, .gr-radio, .gr-file {
    box-shadow: none !important;
    border: 1px solid #dcdcdc !important;
}
"""

########################################
# Construção da Interface Gradio
########################################
# Usamos um tema interno do Gradio, ex: gr.themes.Soft()
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    # Título
    gr.Markdown("<h1 id='title'>Anonimizador com Privacidade Diferencial</h1>")
    
    # Instruções / Passos
    gr.Markdown(
        """
    ### Como funciona:
    1. **Faça o upload de um arquivo (CSV ou Excel).**
    2. **O sistema irá analisar/classificar colunas sensíveis e remover/mascarar o que for necessário.**
    3. **Caso haja colunas sensíveis, você pode aplicar ruído Laplace, desde que seja possível aplicar ruído nesses valores.**
    4. **Se desejar, pode definir um valor customizado de epsilon para a DP.**
    5. **Baixe o arquivo final anonimizado.**
        """
    )


    # Passo 1 - Upload e classificação
    with gr.Group():
        input_file = gr.File(
            label="Selecione o arquivo (CSV ou Excel)",
            file_types=[".csv", ".xlsx", ".xls"]
        )
        classify_btn = gr.Button("Classificar e Pré-Processar",
                                 variant="primary")
        
        # Aqui exibimos a mensagem com colunas DP
        dp_info = gr.Textbox(
            label="Colunas sensíveis para aplicar o ruído Laplace",
            lines=3,
            interactive=False,
            placeholder="(Informações aparecerão aqui após o processamento...)"
        )
        # Guardamos o caminho do arquivo intermediário
        intermediate_file_box = gr.Textbox(
            label="Caminho do Arquivo Intermediário (oculto)",
            visible=False
        )
        # Guardamos a string de colunas DP
        dp_cols_box = gr.Textbox(
            label="dp_cols (oculto)",
            visible=False
        )

        classify_btn.click(
            fn=classify_and_mask,
            inputs=[input_file],
            outputs=[dp_info, intermediate_file_box, dp_cols_box]
        )

    # Passo 2 - Perguntar se aplica DP com valor custom ou não
    with gr.Group():
        gr.Markdown("<h3>Aplicar DP (opcional)</h3>")
        custom_flag = gr.Radio(
            choices=["Não", "Sim"],
            value="Não",
            label="Deseja customizar o epsilon?"
        )
        epsilon_input = gr.Number(
            label="Valor de Epsilon (caso 'Sim')",
            value=1.0
        )

        apply_dp_btn = gr.Button("Aplicar DP e Finalizar",
                                 variant="primary")
        result_info = gr.Textbox(
            label="Resultado",
            interactive=False
        )
        final_file = gr.File(label="Arquivo Final Anonimizado")

        apply_dp_btn.click(
            fn=apply_dp,
            inputs=[intermediate_file_box, dp_cols_box, custom_flag, epsilon_input],
            outputs=[result_info, final_file]
        )

# Executa localmente
if __name__ == "__main__":
    demo.launch()