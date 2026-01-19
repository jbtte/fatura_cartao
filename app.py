import streamlit as st
import utils
from constants import LARGURA_GRAFICO, TAXA_DOLAR_PADRAO

# Importa as novas views
from views import tab_mes, tab_comparador, tab_futuro

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

# Carrega dados
df = utils.carregar_dados()

if df is None:
    st.error("Nenhum arquivo encontrado em data/raw/")
    st.stop()

# --- SIDEBAR & CONTEXTO GLOBAL ---
st.sidebar.header("Configurações")
simular_usd = st.sidebar.checkbox("🇺🇸 Simular em Dólar (USD)")
df_view, moeda = utils.aplicar_conversao_moeda(df, simular_usd, TAXA_DOLAR_PADRAO)

meses = sorted(df_view["MesAno"].unique(), reverse=True)

st.title("📊 Gestão Financeira Analítica")
aba1, aba2, aba3 = st.tabs(["📅 Visão Mensal", "⚖️ Comparador", "🔮 Futuro"])

# --- RENDERIZAÇÃO DAS ABAS ---
# Note como passamos apenas o necessário para cada arquivo

with aba1:
    tab_mes.renderizar(df_view, meses, moeda, LARGURA_GRAFICO)

with aba2:
    tab_comparador.renderizar(df_view, meses, LARGURA_GRAFICO)

with aba3:
    # Para o futuro, precisamos passar o mês atual selecionado na lógica da aba 1?
    # Como as abas são independentes no Streamlit, é melhor deixar o usuário
    # selecionar o mês de referência ou pegar o mais recente.
    # Para simplificar, vou pegar o mês mais recente da lista 'meses' [0]
    # ou criar um seletor local se preferir.
    # Vamos usar o mês mais recente como padrão para projeção futura geral:
    mes_atual = meses[0]
    df_mes_atual = df_view[df_view["MesAno"] == mes_atual]
    tab_futuro.renderizar(df_mes_atual, moeda, LARGURA_GRAFICO)
