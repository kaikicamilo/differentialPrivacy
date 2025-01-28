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

# 📊 Anonimizador com Privacidade Diferencial

Este projeto é uma aplicação **Python** com **Gradio** que permite a anonimização de planilhas com base em técnicas avançadas de **Privacidade Diferencial** e **classificação automática de dados sensíveis** utilizando a **API da OpenAI**. A aplicação é capaz de identificar colunas sensíveis em arquivos Excel ou CSV e realizar o mascaramento ou adição de ruído, garantindo maior segurança e privacidade dos dados.

---

## 📋 Funcionalidades

- **Classificação automática de colunas**:
  - Identifica categorias como identificadores, dados financeiros, demográficos, quase-identificadores, etc.
  - Utiliza a **API da OpenAI** para fornecer uma explicação baseada na **LGPD**.

- **Mascaramento de dados**:
  - Mascaramento parcial em colunas de quase-identificadores (ex.: "Rua dos Bobos, 123" → "Rua d***").

- **Privacidade Diferencial (DP)**:
  - Adiciona ruído Laplace a valores numéricos sensíveis.
  - Permite personalizar o valor de `epsilon` para ajustar o nível de privacidade.

- **Interface Web Amigável**:
  - Upload fácil de arquivos CSV ou Excel.
  - Interface interativa com opções de processamento customizáveis.
  - Download do arquivo anonimizado após o processamento.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **Gradio**: Interface web moderna e responsiva.
- **OpenAI API**: Classificação de dados sensíveis com explicações baseadas na LGPD.
- **NumPy**: Aplicação do ruído Laplace.
- **Pandas**: Manipulação de dados tabulares.
- **Dotenv**: Gerenciamento de variáveis de ambiente.

---

## ⚙️ Como Executar

### 1️⃣ Pré-requisitos

- **Python 3.8 ou superior** instalado.
- Conta ativa na **OpenAI** com uma **API Key**.

### 2️⃣ Instale as dependências

- Execute o comando abaixo para instalar as dependências necessárias:
```bash
pip install -r requirements.txt
```

### 3️⃣ Configure sua chave da API OpenAI

- Crie um arquivo .env na raiz do projeto.
- Adicione sua chave da OpenAI com o formato abaixo:
```python
OPENAI_API_KEY=SuaChaveDaAPI
```

### 4️⃣ Execute o WebApp

- Rode o seguinte comando para iniciar a aplicação localmente:
```bash
python webapp.py
```
- A aplicação estará disponível em [http://127.0.0.1:7860](url).

## 🌟 Funcionalidades Planejadas

- Barra de Progresso: Implementar uma barra para exibir o status do processamento dos arquivos.
- Novos Formatos de Arquivos: Suporte a formatos adicionais além de CSV e Excel.
- Melhorias na Interface: Integração de mensagens mais detalhadas para o usuário durante o processamento.

## 🔒 Segurança

Chaves de API Seguras: A chave da API está armazenada em um arquivo .env que, por sua vez, está no .gitignore e não deve ser incluída no repositório.
- Gestão de Dependências: Utilize o arquivo requirements.txt para gerenciar pacotes e evitar versões desatualizadas ou inseguras.

## 🚀 Funcionalidades Avançadas

- Classificação Automática com OpenAI: A aplicação utiliza prompts dinâmicos enviados ao modelo GPT para analisar exemplos de cada coluna e classificá-los em categorias baseadas na LGPD:
  - Identificador: Ex.: Nome completo, CPF, RG.
  - Quase-Identificador: Ex.: CEP, endereço, data de nascimento.
  - Financeiro: Ex.: Salário, imposto, valor monetário.
  - Demográfico: Ex.: Idade, gênero, número de filhos.

-Privacidade Diferencial: A aplicação de ruído Laplace garante que dados sensíveis sejam protegidos contra identificação direta, ajustando a privacidade através do parâmetro epsilon.

## 🖥️ Estrutura do Projeto

project/
├── anonymize.py         # Lógica de classificação, mascaramento e privacidade diferencial.
├── webapp.py            # Interface Web com Gradio.
├── requirements.txt     # Dependências do projeto.
├── .env                 # Configurações sensíveis (chave da API OpenAI).
└── .gitignore           # Arquivos ignorados pelo Git.


# 🧠 Como o Código Funciona

- O projeto é dividido em duas partes principais: Lógica de processamento e anonimização de dados (anonymize.py). Interface web para interação com o usuário (webapp.py).

## 🔍 Parte 1: Lógica de Anonimização (anonymize.py)

O arquivo anonymize.py contém toda a lógica para classificar, mascarar e adicionar privacidade diferencial às colunas de uma planilha.

### 1️⃣ Carregamento do arquivo 

```python
def carregar_arquivo(file_path):
```

- Lê o arquivo enviado (formato .csv ou .xlsx) e carrega os dados em um DataFrame (estrutura de dados tabular do Pandas).
- Exemplo: Um arquivo Excel com colunas como Nome, CPF, Salário, etc., é transformado em uma tabela manipulável.

### 2️⃣ Classificação de Colunas

```python
def classificar_coluna_com_llm(coluna, exemplos):
```

- Envia uma coluna (e alguns valores de exemplo) para a API da OpenAI, que classifica a coluna em:
  - Identificador: Ex.: CPF, RG, nome completo.
  - Quase-Identificador: Ex.: endereço, CEP, data de nascimento.
  - Financeiro: Ex.: salário, imposto.
  - Demográfico: Ex.: gênero, idade.
  - Texto (não sensível): Dados irrelevantes do ponto de vista de privacidade.
- O modelo também retorna uma explicação detalhada para a classificação, baseada na LGPD.
  - Exemplo:
```json
{
  "tipo_coluna": "financeiro",
  "eh_sensivel": true,
  "explicacao": "Este dado refere-se a valores monetários, que são classificados como sensíveis pela LGPD."
}
```

### 3️⃣ Ações com Base na Classificação

- Após a classificação, diferentes ações são aplicadas com base no tipo da coluna:
  - Identificador: A coluna é removida do arquivo.
  - Quase-Identificador: A coluna é mascarada:
    - Datas: Ajusta o dia para 01 (ex.: 15/03/1990 → 01/03/1990).
    - Textos: Mantém apenas os 5 primeiros caracteres e adiciona *** (ex.: Rua dos Bobos → Rua d***).
  - Financeiro/Demográfico: A coluna é marcada para aplicação de Privacidade Diferencial (DP) em um passo posterior.
  - Texto (não sensível): Nenhuma ação é realizada.
 
### 4️⃣ Aplicação de Privacidade Diferencial

```python
def aplicar_differential_privacy(df, coluna, epsilon=1.0):
```

- Privacidade Diferencial protege valores numéricos sensíveis, como salários, aplicando ruído estatístico (ruído Laplace).
- O parâmetro epsilon controla o nível de ruído:
  - Valores menores de epsilon adicionam mais ruído, protegendo melhor os dados.
  - Valores maiores preservam mais a precisão dos dados, mas com menor proteção.
- Exemplo:
  - Salário Original: [5000, 6000, 7000]
  - Com epsilon=1.0: [5012, 5985, 7034] (com ruído).
  - Com epsilon=0.1: [5200, 5800, 6900] (mais distorcido).
 
### 5️⃣ Salvamento do Arquivo

``` python
def anonimizar_planilha(file_path, output_path=None):
```

- Combina todas as etapas:
  - Lê o arquivo.
  - Classifica as colunas.
  - Aplica remoções/mascaramentos.
  - Salva um arquivo intermediário (sem DP).
- Colunas marcadas para DP são processadas no passo seguinte.

### 6️⃣ Aplicação Final de DP

```python
def aplicar_dp_pos_classificacao(file_path, dp_columns, epsilon=1.0):
```

- Recebe o arquivo intermediário e aplica o ruído Laplace apenas nas colunas marcadas como financeiro ou demográfico.
- Salva o arquivo final anonimizado.


## 🌐 Parte 2: Interface Web (webapp.py)

O arquivo webapp.py é responsável por criar uma interface web interativa usando o Gradio, permitindo que o usuário:

1. Faça o upload de uma planilha.
2. Veja quais colunas são classificadas como sensíveis.
3. Escolha se deseja personalizar o nível de privacidade (valor de epsilon).
4. Baixe o arquivo anonimizado.

### 1️⃣ Upload e Classificação

- O componente gr.File permite ao usuário carregar um arquivo CSV ou Excel.
- A função classify_and_mask processa o arquivo e exibe:
  - Colunas classificadas como sensíveis.
  - Caminho do arquivo intermediário (sem DP).

### 2️⃣ Aplicação de Privacidade Diferencial

- O usuário pode escolher entre usar um valor padrão de epsilon (1.0) ou fornecer um valor personalizado.
- A função apply_dp aplica a DP e gera o arquivo final.

### 3️⃣ Download

- Após o processamento, o arquivo final é disponibilizado para download.

### 4️⃣ Estilo Personalizado

- custom_css:
  - Adiciona bordas arredondadas, cores modernas e um design amigável para o usuário.
  - Destaques:
    - Botões azuis com hover.
    - Upload de arquivo com borda tracejada.
    - Layout centralizado para melhor legibilidade.


# 📚 Fluxo Completo do Código

1. O usuário faz o upload de um arquivo.
2. O sistema classifica as colunas com a API da OpenAI.
   - Identificadores são removidos.
   - Quase-identificadores são mascarados.
   - Colunas sensíveis são marcadas para DP.
3. O usuário escolhe o nível de privacidade (valor de epsilon).
4. A DP é aplicada nas colunas marcadas.
5. O arquivo final é gerado e disponibilizado para download.
