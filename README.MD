# 📊 Gestão Financeira Analítica

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow?style=for-the-badge)

> _Uma ferramenta de Business Intelligence pessoal para transformar dados brutos de faturas de cartão de crédito em prudência financeira e previsibilidade._

---

## 🎯 Sobre o Projeto

Este projeto nasceu da necessidade de ir além do simples "extrato bancário". Enquanto os apps de banco mostram o passado, este dashboard foca no **impacto futuro** das decisões financeiras.

O objetivo é fornecer clareza sobre o **Passivo de Parcelamento** (quanto da renda futura já está comprometida) e analisar comportamentos de consumo para facilitar o planejamento de grandes objetivos familiares, como mudanças internacionais e viagens.

### Principais Diferenciais

- **Cálculo de Passivo Futuro:** Projeta exatamente quanto você deve nos meses seguintes baseado nas parcelas restantes.
- **Análise de Pareto (80/20):** Identifica rapidamente quais estabelecimentos consomem a maior parte do orçamento.
- **Simulação em Dólar (USD):** Um "toggle" instantâneo para converter valores e mentalizar o custo de vida em moeda forte.
- **Comparador Mensal (Delta):** Analisa mês a mês onde houve aumento ou redução de gastos, categoria por categoria.

---

## 🛠️ Tecnologias Utilizadas

O projeto foi construído inteiramente em Python, utilizando uma arquitetura modular:

- **[Streamlit](https://streamlit.io/):** Framework para construção da interface web interativa.
- **[Pandas](https://pandas.pydata.org/):** Motor de processamento e limpeza de dados (ETL).
- **[Plotly Express](https://plotly.com/python/):** Biblioteca para gráficos interativos e responsivos.
- **[Matplotlib](https://matplotlib.org/):** Utilizado para estilização condicional (gradientes) em tabelas de dados.

---

## 📂 Estrutura do Projeto

A organização segue princípios de engenharia de software para garantir escalabilidade e manutenção:

```text
fatura_cartao/
├── app.py              # Camada de Apresentação (Interface Visual)
├── utils.py            # Camada Lógica (Processamento de dados e Cálculos)
├── constants.py        # Configurações estáticas e parâmetros
├── requirements.txt    # Dependências do projeto
├── .gitignore          # Proteção de dados sensíveis
└── data/
    └── raw/            # Diretório para depósito dos CSVs das faturas
```

## 📋 Estrutura do Arquivo CSV

Para que o dashboard funcione corretamente, o arquivo `.csv` deve conter as seguintes colunas (o separador pode ser vírgula ou ponto-e-vírgula):

| Coluna              | Tipo     | Descrição                                                          | Exemplo       |
| :------------------ | :------- | :----------------------------------------------------------------- | :------------ |
| **Data**            | Data     | Data da compra (DD/MM/AAAA ou YYYY-MM-DD).                         | `2025-11-17`  |
| **MesAno**          | Texto    | Mês de referência da fatura (formato YYYY-MM). Usado para filtros. | `2026-01`     |
| **Estabelecimento** | Texto    | Nome da loja ou serviço.                                           | `Clube Wine`  |
| **Categoria**       | Texto    | Agrupamento principal (ex: Alimentação, Transporte).               | `Alimentação` |
| **Subcategoria**    | Texto    | Detalhe opcional (ex: Restaurante, Mercado).                       | `Vinhos`      |
| **Valor_R$**        | Numérico | Valor da parcela ou compra. Pode usar vírgula ou ponto.            | `69,65`       |
| **ParcelaAtual**    | Inteiro  | Número da parcela sendo paga neste mês.                            | `1`           |
| **TotalParcelas**   | Inteiro  | Em quantas vezes a compra foi dividida.                            | `1`           |

# 📊 Gestão Financeira Analítica v2.0

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Modular_Views-blue?style=for-the-badge)

Dashboard de BI (Business Intelligence) focado em **Prudência Financeira** e planejamento de longo prazo, como imigração para os EUA e viagens internacionais [cite: 2025-07-04, 2026-01-13].

---

## 🏗️ Arquitetura do Sistema

O projeto utiliza uma separação rigorosa entre lógica e interface para garantir manutenibilidade [cite: 2026-01-19]:

- **`app.py`**: Gerencia o estado global e a navegação por abas [cite: 2026-01-19].
- **`utils.py`**: Concentra toda a inteligência matemática, limpeza de dados e métricas de tendência [cite: 2026-01-19].
- **`views/`**: Contém os arquivos `tab_mes.py`, `tab_comparador.py` e `tab_futuro.py`, permitindo evoluir cada aba isoladamente [cite: 2026-01-19].
- **`constants.py`**: Centraliza parâmetros como a lista de gastos essenciais e taxas de câmbio [cite: 2026-01-19].

---

## 🌟 Novas Funcionalidades (v2.0)

### 1. Raio-X Hierárquico (Sunburst)

Visualização em múltiplos níveis que permite identificar, por exemplo, quanto da categoria **Alimentação** foi destinado a **Mercado** (Essencial) vs. **Restaurantes** (Estilo de Vida) [cite: 2026-01-19].

### 2. Inteligência de Contexto

Na aba de comparação, o sistema calcula automaticamente [cite: 2026-01-19]:

- **Delta vs. Mês Anterior:** Variação nominal do gasto [cite: 2026-01-19].
- **Média Semestral:** Compara o gasto atual com a média dos últimos 6 meses para identificar anomalias [cite: 2026-01-19].

### 3. Mapa de Desalavancagem

Detalhamento de compras parceladas incluindo [cite: 2026-01-19]:

- Valor total original da compra [cite: 2026-01-19].
- Data prevista para a última parcela (mês/ano) [cite: 2026-01-19].
- Métricas de amortização (Quanto da fatura atual é dívida antiga vs. novos gastos) [cite: 2026-01-19].

---

## 📋 Requisitos de Dados (CSV)

O arquivo deve ser depositado em `data/raw/` com as colunas [cite: 2026-01-19]:
`Data, MesAno, Estabelecimento, Categoria, Subcategoria, Valor_R$, ParcelaAtual, TotalParcelas` [cite: 2026-01-19].

---

## 🚀 Como Executar

1.  Ative o ambiente virtual: `source venv/bin/activate` [cite: 2026-01-19].
2.  Instale as dependências: `pip install streamlit pandas plotly matplotlib` [cite: 2026-01-19].
3.  Execute: `streamlit run app.py` [cite: 2026-01-19].

---

_Foco em Ordem, Família e Futuro._
