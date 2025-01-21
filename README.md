# Anonimizador de Planilhas

Este projeto é uma aplicação **Flask** para anonimização de planilhas. Utilizando a API da OpenAI, o sistema analisa os dados de um arquivo Excel ou CSV enviado pelo usuário e realiza a classificação de colunas. Dados sensíveis podem ser anonimizados ou removidos com base na sua categoria, garantindo maior segurança e privacidade.

---

## 📋 Funcionalidades

- **Classificação de colunas sensíveis**: Identifica categorias como identificadores, financeiros, demográficos, etc.
- **Mascaramento de dados**: Realiza mascaramento parcial em colunas de quase-identificadores.
- **Privacidade diferencial**: Adiciona ruído a valores numéricos sensíveis.
- **Download de arquivos anonimizados**: Gera uma nova planilha para download com os dados processados.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **Flask**
- **OpenAI API**
- **NumPy**
- **Pandas**
- **Bootstrap 5** (para front-end)

---

## ⚙️ Como Executar

### 1️⃣ Pré-requisitos
- Python 3.8 ou superior instalado.
- Conta ativa na OpenAI com uma API Key.

### 2️⃣ Instale as dependências
- pip install -r requirements.txt

### 3️⃣ Configure sua chave da API OpenAI
- Crie um arquivo .env na raiz do projeto.
- Padrão .env: OPENAI_API_KEY=[CHAVEAPIOPENAI]
- Adicione sua chave no arquivo .env.

---

## 🔒 Segurança
- Variáveis de ambiente: Certifique-se de que sua chave da API está armazenada no arquivo .env e que o .env está listado no .gitignore para evitar vazamentos.
- Dependências seguras: Use o arquivo requirements.txt para evitar versões inseguras de pacotes.

## 🌟 Funcionalidade Planejada
- Melhoria na interface: Implementar barra de progresso durante o processamento dos arquivos.
- Permitir valores personalisados de ruído.
- Suporte a novos formatos de arquivos: Adicionar compatibilidade com mais formatos além de CSV e Excel.
