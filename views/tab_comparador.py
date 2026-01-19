import streamlit as st
import plotly.express as px
import utils


# Adicionado parâmetro 'moeda'
def renderizar(df_view, meses, moeda, largura_grafico):
    st.subheader("⚖️ Duelo de Meses & Tendência")

    c1, c2 = st.columns(2)
    mes_a = c1.selectbox("Mês Referência (A)", meses, index=1 if len(meses) > 1 else 0)
    mes_b = c2.selectbox("Mês Comparação (B)", meses, index=0)

    # --- KPI DE CONTEXTO (Métrica que você pediu) ---
    # Analisa o Mês A em relação ao histórico
    if mes_a:
        atual, anterior, media_6m = utils.calcular_metricas_contexto(df_view, mes_a)

        st.markdown(f"**Contexto do Mês {mes_a}:**")
        k1, k2, k3 = st.columns(3)

        # 1. Valor x Anterior
        delta_anterior = atual - anterior
        k1.metric(
            f"Total {mes_a}",
            f"{moeda} {atual:,.2f}",
            f"{delta_anterior:,.2f} vs mês anterior",
            delta_color="inverse",
        )

        # 2. Valor x Média
        delta_media = atual - media_6m if media_6m > 0 else 0
        k3.metric(
            "vs. Média (6m)",
            f"{moeda} {media_6m:,.2f}",
            f"{delta_media:,.2f}",
            delta_color="inverse",
            help="Comparado à média dos 6 meses anteriores",
        )

        # 3. Comparação Direta A vs B (KPI Simples)
        if mes_b:
            val_b = df_view[df_view["MesAno"] == mes_b]["Valor_View"].sum()
            delta_ab = atual - val_b
            k2.metric(
                f"vs. Mês {mes_b}",
                f"{moeda} {val_b:,.2f}",
                f"{delta_ab:,.2f} (A - B)",
                delta_color="inverse",
            )

    st.markdown("---")

    # --- GRÁFICOS COMPARATIVOS (Lógica anterior) ---
    if mes_a and mes_b:
        df_comp = df_view[df_view["MesAno"].isin([mes_a, mes_b])]

        fig_comp = px.bar(
            df_comp.groupby(["Categoria", "MesAno"])["Valor_View"].sum().reset_index(),
            x="Categoria",
            y="Valor_View",
            color="MesAno",
            barmode="group",
            title=f"Comparativo Visual: {mes_a} vs {mes_b}",
        )
        st.plotly_chart(fig_comp, width=largura_grafico)

        st.markdown("#### Detalhe da Variação")
        df_delta = utils.calcular_delta_meses(df_view, mes_a, mes_b)
        st.dataframe(df_delta.style.format("{:.2f}"), width=largura_grafico)
