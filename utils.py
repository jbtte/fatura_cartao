import pandas as pd
import glob
import os
import streamlit as st
from constants import CATS_ESSENCIAIS


@st.cache_data
def carregar_dados():
    caminho = os.path.join("data", "raw", "*.csv")
    arquivos = glob.glob(caminho)

    if not arquivos:
        return None

    lista_dfs = [pd.read_csv(f, sep=None, engine="python") for f in arquivos]
    df = pd.concat(lista_dfs, ignore_index=True)

    # 1. LIMPEZA DE TEXTO (Padronização)
    colunas_texto = ["Estabelecimento", "Categoria", "Subcategoria"]
    for col in colunas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # 2. TRATAMENTO NUMÉRICO
    if df["Valor_R$"].dtype == "object":
        df["Valor_R$"] = df["Valor_R$"].str.replace(",", ".").astype(float)

    df["ParcelaAtual"] = (
        pd.to_numeric(df["ParcelaAtual"], errors="coerce").fillna(0).astype(int)
    )
    df["TotalParcelas"] = (
        pd.to_numeric(df["TotalParcelas"], errors="coerce").fillna(0).astype(int)
    )

    # 3. CÁLCULOS DE NEGÓCIO (Aqui estava o erro: essas linhas são obrigatórias)
    df["Passivo_Futuro"] = (df["TotalParcelas"] - df["ParcelaAtual"]) * df["Valor_R$"]

    # Classificação Essencial vs Estilo de Vida
    if "Categoria" in df.columns:
        df["Tipo_Gasto"] = df["Categoria"].apply(
            lambda x: "Essencial" if x in CATS_ESSENCIAIS else "Estilo de Vida"
        )
    else:
        df["Tipo_Gasto"] = "Indefinido"

    return df


def aplicar_conversao_moeda(df, simular_usd, taxa):
    """Gera visualização com moeda convertida"""
    df_view = df.copy()
    fator = 1 / taxa if simular_usd else 1

    df_view["Valor_View"] = df_view["Valor_R$"] * fator

    # Garante que a coluna existe antes de multiplicar
    if "Passivo_Futuro" in df_view.columns:
        df_view["Passivo_View"] = df_view["Passivo_Futuro"] * fator
    else:
        df_view["Passivo_View"] = 0.0

    return df_view, "USD" if simular_usd else "BRL"


def calcular_delta_meses(df, mes_a, mes_b):
    """Gera o dataframe comparativo para a aba 2"""
    resumo_a = df[df["MesAno"] == mes_a].groupby("Categoria")["Valor_View"].sum()
    resumo_b = df[df["MesAno"] == mes_b].groupby("Categoria")["Valor_View"].sum()

    df_delta = pd.DataFrame(
        {f"Valor {mes_a}": resumo_a, f"Valor {mes_b}": resumo_b}
    ).fillna(0)
    df_delta["Diferença"] = df_delta[f"Valor {mes_b}"] - df_delta[f"Valor {mes_a}"]
    return df_delta.sort_values("Diferença", ascending=False)


def processar_dados_futuros(df_mes):
    """Lógica complexa da aba de projeção futura (Aba 3)"""
    if df_mes.empty:
        return None, None

    # Filtra apenas o que tem parcelas pendentes
    ativos = df_mes[df_mes["TotalParcelas"] > df_mes["ParcelaAtual"]].copy()

    if ativos.empty:
        return None, None

    # --- LÓGICA DA TABELA ---
    ativos["Valor_Total_Compra"] = ativos["Valor_View"] * ativos["TotalParcelas"]

    # Converte MesAno para datetime para somar meses
    ativos["Data_Ref"] = pd.to_datetime(ativos["MesAno"].astype(str) + "-01")
    ativos["Meses_Restantes"] = ativos["TotalParcelas"] - ativos["ParcelaAtual"]

    # Calcula data final
    ativos["Data_Final"] = ativos.apply(
        lambda x: x["Data_Ref"] + pd.DateOffset(months=x["Meses_Restantes"]), axis=1
    )
    ativos["Ultima_Parcela_Fmt"] = ativos["Data_Final"].dt.strftime("%m/%Y")

    df_tabela = ativos[
        [
            "Estabelecimento",
            "Valor_Total_Compra",
            "Valor_View",
            "TotalParcelas",
            "ParcelaAtual",
            "Ultima_Parcela_Fmt",
            "Data_Final",  # Mantém para ordenação, mas não precisa exibir se não quiser
        ]
    ].sort_values(by="Data_Final", ascending=False)

    # --- LÓGICA DO GRÁFICO ---
    projecao = []
    for _, row in ativos.iterrows():
        faltam = int(row["Meses_Restantes"])
        for i in range(1, faltam + 1):
            projecao.append({"Meses_Frente": i, "Valor": row["Valor_View"]})

    if projecao:
        df_grafico = pd.DataFrame(projecao).groupby("Meses_Frente").sum().reset_index()
    else:
        df_grafico = pd.DataFrame()

    return df_tabela, df_grafico
