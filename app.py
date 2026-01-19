import streamlit as st
import utils
from constants import LARGURA_GRAFICO, TAXA_DOLAR_PADRAO

# Importa as views que criamos
from views import tab_mes, tab_comparador, tab_futuro

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

# Carrega a base de dados
df = utils.carregar_dados()

if df is None:
    st.error("Nenhum arquivo encontrado em data/raw/")
    st.stop()

# --- SIDEBAR (BARRA LATERAL) ---
st.sidebar.header("Configurações")

# 1. Definição da lista de meses (Ordenada do mais recente para o antigo)
meses = sorted(df["MesAno"].unique(), reverse=True)

# 2. SELETOR GLOBAL DE MÊS (Aqui nasce a variável 'mes_ref_global')
# É esta variável que vai controlar o que aparece nas abas 1 e 3
mes_ref_global = st.sidebar.selectbox("📅 Mês de Referência", meses)

# 3. Configuração de Moeda
simular_usd = st.sidebar.checkbox("🇺🇸 Simular em Dólar (USD)")

# Aplica a conversão de moeda nos dados
df_view, moeda = utils.aplicar_conversao_moeda(df, simular_usd, TAXA_DOLAR_PADRAO)

# --- ÁREA PRINCIPAL ---
st.title("📊 Gestão Financeira Analítica")

# Criação das Abas
aba1, aba2, aba3 = st.tabs(["📅 Visão Mensal", "⚖️ Comparador", "🔮 Futuro & Dívida"])

# --- RENDERIZAÇÃO DAS ABAS ---

with aba1:
    # Passamos o mês selecionado na sidebar (mes_ref_global)
    tab_mes.renderizar(df_view, mes_ref_global, moeda, LARGURA_GRAFICO)

with aba2:
    # A aba comparador tem seus próprios seletores, então passamos apenas a lista de opções 'meses'
    # E agora também passamos a 'moeda' para os KPIs funcionarem
    tab_comparador.renderizar(df_view, meses, moeda, LARGURA_GRAFICO)

with aba3:
    # Filtramos os dados apenas para o mês selecionado globalmente
    df_mes_atual = df_view[df_view["MesAno"] == mes_ref_global]
    # Renderiza a aba futuro com os dados desse mês
    tab_futuro.renderizar(df_mes_atual, moeda, LARGURA_GRAFICO)
