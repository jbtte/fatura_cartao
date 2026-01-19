import streamlit as st
import plotly.express as px
import utils
from constants import LARGURA_GRAFICO, TAXA_DOLAR_PADRAO
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

# Carrega dados via utils
df = utils.carregar_dados()

if df is None:
    st.error("Nenhum arquivo encontrado em data/raw/")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("Configurações")
simular_usd = st.sidebar.checkbox("🇺🇸 Simular em Dólar (USD)")
df_view, moeda = utils.aplicar_conversao_moeda(df, simular_usd, TAXA_DOLAR_PADRAO)

st.title("📊 Gestão Financeira Analítica")
tab_mes, tab_comparador, tab_projecao = st.tabs(
    ["📅 Visão Mensal", "⚖️ Comparador", "🔮 Futuro"]
)

# --- ABA 1: VISÃO MENSAL ---
with tab_mes:
    meses = sorted(df_view["MesAno"].unique(), reverse=True)
    mes_ref = st.selectbox("Selecione o Mês", meses)
    df_mes = df_view[df_view["MesAno"] == mes_ref]

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Total Gasto ({moeda})", f"{df_mes['Valor_View'].sum():,.2f}")
    c2.metric("Itens", len(df_mes))
    c3.metric(f"Passivo Criado", f"{df_mes['Passivo_View'].sum():,.2f}")

    # Insight Essencial
    total = df_mes["Valor_View"].sum()
    essencial = df_mes[df_mes["Tipo_Gasto"] == "Essencial"]["Valor_View"].sum()
    pct = (essencial / total * 100) if total > 0 else 0
    c4.metric("% Essencial", f"{pct:.1f}%")

    st.markdown("---")

    # Gráficos Principais
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_cat = px.bar(
            df_mes.groupby("Categoria")["Valor_View"].sum().reset_index(),
            x="Categoria",
            y="Valor_View",
            color="Categoria",
            text_auto=".0f",
        )
        st.plotly_chart(fig_cat, width=LARGURA_GRAFICO)

    with col_g2:
        fig_pie = px.pie(
            df_mes,
            values="Valor_View",
            names="Tipo_Gasto",
            hole=0.4,
            color_discrete_map={"Essencial": "#2E86C1", "Estilo de Vida": "#E74C3C"},
        )
        st.plotly_chart(fig_pie, width=LARGURA_GRAFICO)

    # --- NOVO: ANÁLISE COMPORTAMENTAL ---
    st.markdown("---")
    st.subheader("🕵️ Análise Comportamental")

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        # 1. TOP 5 ESTABELECIMENTOS (PARETO)
        st.caption("Top 5 Lugares onde você mais gasta")
        top_places = (
            df_mes.groupby("Estabelecimento")["Valor_View"]
            .sum()
            .nlargest(5)
            .reset_index()
        )

        fig_pareto = px.bar(
            top_places,
            x="Valor_View",
            y="Estabelecimento",
            orientation="h",
            text_auto=".0f",
            color="Valor_View",
            color_continuous_scale="Reds",
        )
        # Inverte eixo Y para o maior ficar em cima
        fig_pareto.update_layout(
            yaxis={"categoryorder": "total ascending"}, showlegend=False
        )
        st.plotly_chart(fig_pareto, width=LARGURA_GRAFICO)

    with col_b2:
        # 2. GASTOS POR DIA DA SEMANA
        st.caption("Em qual dia da semana eu gasto mais?")
        # Converte Data
        df_mes["Data"] = pd.to_datetime(df_mes["Data"])
        df_mes["Dia_Semana"] = df_mes["Data"].dt.day_name()

        # Mapeamento para PT-BR (Opcional, mas fica mais bonito)
        dias_traduzidos = {
            "Monday": "Segunda",
            "Tuesday": "Terça",
            "Wednesday": "Quarta",
            "Thursday": "Quinta",
            "Friday": "Sexta",
            "Saturday": "Sábado",
            "Sunday": "Domingo",
        }
        df_mes["Dia_Semana"] = df_mes["Dia_Semana"].map(dias_traduzidos)

        ordem_dias = [
            "Segunda",
            "Terça",
            "Quarta",
            "Quinta",
            "Sexta",
            "Sábado",
            "Domingo",
        ]

        # Agrupa e reordena
        gastos_dia = (
            df_mes.groupby("Dia_Semana")["Valor_View"]
            .sum()
            .reindex(ordem_dias)
            .reset_index()
        )

        fig_week = px.bar(
            gastos_dia,
            x="Dia_Semana",
            y="Valor_View",
            color_discrete_sequence=["#F1C40F"],
        )  # Amarelo "Alerta"
        st.plotly_chart(fig_week, width=LARGURA_GRAFICO)

    # Tabela Filtrada
    st.markdown("---")
    st.subheader("Extrato Detalhado")
    cats = df_mes["Categoria"].unique()
    filtro = st.multiselect("Filtrar Categoria:", cats, default=cats)
    st.dataframe(df_mes[df_mes["Categoria"].isin(filtro)], width=LARGURA_GRAFICO)

# --- ABA 2: COMPARADOR ---
with tab_comparador:
    c1, c2 = st.columns(2)
    mes_a = c1.selectbox("Mês Referência", meses, index=1 if len(meses) > 1 else 0)
    mes_b = c2.selectbox("Mês Comparação", meses, index=0)

    if mes_a and mes_b:
        df_comp = df_view[df_view["MesAno"].isin([mes_a, mes_b])]
        fig_comp = px.bar(
            df_comp.groupby(["Categoria", "MesAno"])["Valor_View"].sum().reset_index(),
            x="Categoria",
            y="Valor_View",
            color="MesAno",
            barmode="group",
        )
        st.plotly_chart(fig_comp, width=LARGURA_GRAFICO)

        st.markdown("#### Detalhe da Variação")
        df_delta = utils.calcular_delta_meses(df_view, mes_a, mes_b)
        # Código seguro sem gradiente para evitar erro do matplotlib se não estiver carregado
        st.dataframe(df_delta.style.format("{:.2f}"), width=LARGURA_GRAFICO)

# --- ABA 3: FUTURO ---
with tab_projecao:
    projecao = []
    for _, row in df[df["TotalParcelas"] > df["ParcelaAtual"]].iterrows():
        faltam = int(row["TotalParcelas"] - row["ParcelaAtual"])
        for i in range(1, faltam + 1):
            valor_ajustado = row["Valor_R$"] * (
                1 / TAXA_DOLAR_PADRAO if simular_usd else 1
            )
            projecao.append({"Meses_Frente": i, "Valor": valor_ajustado})

    if projecao:
        df_proj = pd.DataFrame(projecao).groupby("Meses_Frente").sum().reset_index()
        fig_proj = px.area(
            df_proj,
            x="Meses_Frente",
            y="Valor",
            title=f"Fluxo de Caixa Comprometido ({moeda})",
        )
        st.plotly_chart(fig_proj, width=LARGURA_GRAFICO)
    else:
        st.success("Sem dívidas futuras!")
