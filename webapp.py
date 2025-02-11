import os
import tempfile
import logging
from typing import Tuple, Optional

import gradio as gr
from dotenv import load_dotenv

from anonymize import (
    anonimizar_planilha,
    aplicar_dp_pos_classificacao
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

########################################
# Passo 1: classificar e gerar arquivo intermediário
########################################
def classify_and_mask(uploaded_file) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Recebe o arquivo do usuário e chama `anonimizar_planilha`.
    Retorna (msg, caminho_do_arquivo_intermediario, string_com_colunas_dp).
    """
    if not uploaded_file:
        return None, None, None

    input_path = uploaded_file.name
    tmpdir = tempfile.mkdtemp()
    output_path = os.path.join(tmpdir, "intermediario.xlsx")

    dp_cols, saved_file = anonimizar_planilha(
        file_path=input_path,
        output_path=output_path
    )

    if saved_file is None:
        return "Erro ao processar arquivo.", None, None

    if len(dp_cols) == 0:
        msg = "Nenhuma coluna sensível encontrada para DP."
    else:
        msg = (
            "Colunas sensíveis (podem ter ruído Laplace aplicado):\n"
            f"{', '.join(dp_cols)}"
        )

    return msg, saved_file, ",".join(dp_cols)

########################################
# Passo 2: aplicar DP (opcional)
########################################
def apply_dp(
    intermediate_file: str,
    dp_cols_str: str,
    custom_flag: str,
    epsilon_value: float
) -> Tuple[str, Optional[str]]:
    """
    Aplica ruído Laplace nas colunas marcadas como sensíveis.
    """
    if not intermediate_file:
        return "Nenhum arquivo intermediário para processar.", None

    if not dp_cols_str:
        return "Nenhuma coluna DP-eligível detectada.", intermediate_file

    dp_columns = [c.strip() for c in dp_cols_str.split(",") if c.strip()]
    if len(dp_columns) == 0:
        return "Nenhuma coluna DP-eligível detectada (lista vazia).", intermediate_file

    if custom_flag == "Sim":
        try:
            epsilon = float(epsilon_value)
        except ValueError:
            epsilon = 1.0
    else:
        epsilon = 1.0

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
# CSS Customizado e Interface
########################################
custom_css = """
/* Exemplo de customização CSS */
body {
    font-family: 'Inter', sans-serif;
    background: #f2f2f2;
    color: #333;
    margin: 0;
    padding: 0;
}
...
"""

with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown("<h1 id='title'>Anonimizador com Privacidade Diferencial</h1>")
    gr.Markdown("""
    ### Como funciona:
    1. **Faça o upload de um arquivo (CSV ou Excel).**
    2. **O sistema classifica colunas sensíveis e remove/mascara dados pessoais.**
    3. **Se houver colunas numéricas sensíveis, você pode aplicar ruído Laplace (DP).**
    4. **Você pode definir um valor customizado de epsilon para ajustar o nível de privacidade.**
    5. **Baixe o arquivo final anonimizado.**
    """)

    with gr.Group():
        input_file = gr.File(
            label="Selecione o arquivo (CSV/Excel)",
            file_types=[".csv", ".xlsx", ".xls"]
        )
        classify_btn = gr.Button("Classificar e Pré-Processar")
        dp_info = gr.Textbox(
            label="Colunas sensíveis para DP",
            lines=3,
            interactive=False
        )
        intermediate_file_box = gr.Textbox(
            label="Caminho Intermediário (oculto)",
            visible=False
        )
        dp_cols_box = gr.Textbox(
            label="dp_cols (oculto)",
            visible=False
        )

        classify_btn.click(
            fn=classify_and_mask,
            inputs=[input_file],
            outputs=[dp_info, intermediate_file_box, dp_cols_box]
        )

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

        apply_dp_btn = gr.Button("Aplicar DP e Finalizar")
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

if __name__ == "__main__":
    demo.launch()