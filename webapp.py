# webapp.py

import os
import tempfile

import gradio as gr
from anonymize import anonimizar_planilha
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env (caso você precise delas)
load_dotenv()

def process_file(uploaded_file):
    """
    Recebe o arquivo carregado pelo usuário,
    chama a função de anonimização e retorna o arquivo final.
    """
    if not uploaded_file:
        return None

    # O Gradio salva o arquivo em um caminho temporário, no .name
    input_path = uploaded_file.name
    
    # Cria um diretório temporário para salvar o arquivo anonimizado
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "anonimizado.xlsx")
        
        # Chama a função de anonimização (que retorna o caminho final salvo)
        result_path = anonimizar_planilha(input_path, output_path=output_path)
        
        if result_path and os.path.exists(result_path):
            # Se deu certo, retorna o caminho gerado para Gradio
            return result_path
        else:
            # Caso haja algum erro, retorna None
            return None

# Monta a interface do Gradio
with gr.Blocks() as demo:
    gr.Markdown("# Anonimizador com Privacidade Diferencial")
    gr.Markdown("""
Faça o upload de um arquivo (CSV ou Excel) para anonimização.
O sistema aplica técnicas baseadas em LGPD e Privacidade Diferencial.
Você poderá baixar o arquivo resultante em seguida.
    """)

    # Componente de upload: aceita .csv, .xlsx, .xls etc.
    input_file = gr.File(
        label="Selecione o arquivo",
        file_types=[".csv", ".xlsx", ".xls"]
    )

    # Componente para download do arquivo final
    output_file = gr.File(label="Arquivo Anonimizado")

    # Botão para iniciar o processo
    process_button = gr.Button("Processar")

    # Quando o usuário clica no botão, chama a função `process_file`
    # e envia o resultado para `output_file` (fazendo download)
    process_button.click(
        fn=process_file,
        inputs=[input_file],
        outputs=[output_file]
    )

# Executa a aplicação localmente
if __name__ == "__main__":
    # Por padrão, `demo.launch()` inicia em http://127.0.0.1:7860
    demo.launch()