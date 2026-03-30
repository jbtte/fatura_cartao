import streamlit as st
import utils
from constants import LARGURA_GRAFICO

from views import tab_mes, tab_comparador, tab_futuro, tab_alertas

st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

df = utils.carregar_dados(_cache_key=utils._cache_key_csvs())

if df is None:
    st.error("Nenhum arquivo encontrado em data/raw/")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("Configurações")

meses = sorted(df["MesAno"].unique(), reverse=True)
mes_ref_global = st.sidebar.selectbox("📅 Mês de Referência", meses)

# --- ÁREA PRINCIPAL ---
st.title("📊 Gestão Financeira Analítica")

aba1, aba2, aba3, aba4 = st.tabs(["📅 Visão Mensal", "⚖️ Comparador", "🔮 Futuro & Dívida", "⚠️ Alertas"])

with aba1:
    tab_mes.renderizar(df, mes_ref_global, LARGURA_GRAFICO)

with aba2:
    tab_comparador.renderizar(df, meses, LARGURA_GRAFICO)

with aba3:
    df_mes_atual = df[df["MesAno"] == mes_ref_global]
    tab_futuro.renderizar(df_mes_atual, LARGURA_GRAFICO)

with aba4:
    tab_alertas.renderizar(df, mes_ref_global, LARGURA_GRAFICO)
