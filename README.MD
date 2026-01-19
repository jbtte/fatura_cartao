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
