# utils.py
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

    # Tratamento de Tipos
    if df["Valor_R$"].dtype == "object":
        df["Valor_R$"] = df["Valor_R$"].str.replace(",", ".").astype(float)

    df["ParcelaAtual"] = (
        pd.to_numeric(df["ParcelaAtual"], errors="coerce").fillna(0).astype(int)
    )
    df["TotalParcelas"] = (
        pd.to_numeric(df["TotalParcelas"], errors="coerce").fillna(0).astype(int)
    )

    # Cálculos de Negócio
    df["Passivo_Futuro"] = (df["TotalParcelas"] - df["ParcelaAtual"]) * df["Valor_R$"]
    df["Tipo_Gasto"] = df["Categoria"].apply(
        lambda x: "Essencial" if x in CATS_ESSENCIAIS else "Estilo de Vida"
    )

    return df


def aplicar_conversao_moeda(df, simular_usd, taxa):
    """Retorna uma cópia do DF com valores ajustados para a moeda escolhida"""
    df_view = df.copy()
    fator = 1 / taxa if simular_usd else 1

    df_view["Valor_View"] = df_view["Valor_R$"] * fator
    df_view["Passivo_View"] = df_view["Passivo_Futuro"] * fator

    return df_view, "USD" if simular_usd else "BRL"


def calcular_delta_meses(df, mes_a, mes_b):
    """Gera o dataframe comparativo entre dois meses"""
    resumo_a = df[df["MesAno"] == mes_a].groupby("Categoria")["Valor_View"].sum()
    resumo_b = df[df["MesAno"] == mes_b].groupby("Categoria")["Valor_View"].sum()

    df_delta = pd.DataFrame(
        {f"Valor {mes_a}": resumo_a, f"Valor {mes_b}": resumo_b}
    ).fillna(0)
    df_delta["Diferença"] = df_delta[f"Valor {mes_b}"] - df_delta[f"Valor {mes_a}"]
    return df_delta.sort_values("Diferença", ascending=False)
