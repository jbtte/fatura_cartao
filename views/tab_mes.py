import streamlit as st
import plotly.express as px
import pandas as pd
import utils


def renderizar(df_view, mes_ref, largura_grafico):
    df_mes = df_view[df_view["MesAno"] == mes_ref].copy()

    if df_mes.empty:
        st.warning(f"Sem dados para o mês {mes_ref}.")
        return

    # --- ALERTA DE GASTO ACIMA DA MÉDIA ---
    _, _, media_6m = utils.calcular_metricas_contexto(df_view, mes_ref)
    total_mes = df_mes["Valor_View"].sum()
    if media_6m > 0 and total_mes > media_6m * 1.15:
        pct_acima = (total_mes / media_6m - 1) * 100
        st.warning(
            f"⚠️ Mês {pct_acima:.0f}% acima da média histórica dos últimos 6 meses "
            f"(R$ {media_6m:,.2f})"
        )

    # --- KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Gasto (R$)", f"{total_mes:,.2f}")
    c2.metric("Itens", len(df_mes))
    c3.metric("Passivo Criado (R$)", f"{df_mes['Passivo_View'].sum():,.2f}")

    essencial = df_mes[df_mes["Tipo_Gasto"] == "Essencial"]["Valor_View"].sum()
    pct = (essencial / total_mes * 100) if total_mes > 0 else 0
    c4.metric("% Essencial", f"{pct:.1f}%")

    st.markdown("---")

    # --- GRÁFICOS PRINCIPAIS ---
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Raio-X: Categoria > Subcategoria")
        fig_sun = px.sunburst(
            df_mes[df_mes["Valor_View"] > 0],
            path=["Categoria", "Subcategoria"],
            values="Valor_View",
            color="Categoria",
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        st.plotly_chart(fig_sun, width=largura_grafico)

    with col_g2:
        st.subheader("Essencial vs Estilo de Vida")
        fig_pie = px.pie(
            df_mes,
            values="Valor_View",
            names="Tipo_Gasto",
            hole=0.4,
            color_discrete_map={"Essencial": "#2E86C1", "Estilo de Vida": "#E74C3C"},
        )
        st.plotly_chart(fig_pie, width=largura_grafico)

    # --- ANÁLISE COMPORTAMENTAL ---
    st.markdown("---")
    st.subheader("🕵️ Análise Comportamental")

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.caption("Top 5 Lugares (Pareto)")
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
            labels={"Valor_View": "R$"},
        )
        fig_pareto.update_layout(
            yaxis={"categoryorder": "total ascending"}, showlegend=False
        )
        st.plotly_chart(fig_pareto, width=largura_grafico)

    with col_b2:
        st.caption("Gastos por Dia do Mês")
        gastos_dia = (
            df_mes.groupby(df_mes["Data"].dt.day)["Valor_View"]
            .sum()
            .reset_index()
        )
        gastos_dia.columns = ["Dia", "Valor"]
        fig_day = px.bar(
            gastos_dia,
            x="Dia",
            y="Valor",
            color_discrete_sequence=["#F1C40F"],
            labels={"Dia": "Dia do Mês", "Valor": "R$"},
        )
        fig_day.update_layout(xaxis=dict(tickmode="linear", dtick=1))
        st.plotly_chart(fig_day, width=largura_grafico)

    # --- DRILL DOWN DETALHADO ---
    st.markdown("---")
    st.subheader("🔬 Microscópio de Gastos")

    cats = sorted(df_mes["Categoria"].unique())
    filtro_cats = st.multiselect("Focar em Categorias específicas:", cats)

    if filtro_cats:
        df_focado = df_mes[df_mes["Categoria"].isin(filtro_cats)]
        st.markdown(f"**Detalhamento de: {', '.join(filtro_cats)}**")

        fig_sub = px.bar(
            df_focado.groupby("Subcategoria")["Valor_View"]
            .sum()
            .reset_index()
            .sort_values("Valor_View", ascending=False),
            x="Subcategoria",
            y="Valor_View",
            text_auto=".2f",
            title="Onde exatamente foi o dinheiro?",
            labels={"Valor_View": "R$"},
        )
        st.plotly_chart(fig_sub, width=largura_grafico)

        st.dataframe(
            df_focado[["Data", "Estabelecimento", "Subcategoria", "Cartao", "Valor_View"]]
            .sort_values(["Subcategoria", "Valor_View"], ascending=[True, False])
            .reset_index(drop=True),
            column_config={
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Valor_View": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "Cartao": "Cartão",
            },
            use_container_width=True,
        )
    else:
        st.caption("Top 10 transações do mês")
        top10 = (
            df_mes[["Data", "Estabelecimento", "Categoria", "Subcategoria", "Cartao", "Valor_View"]]
            .sort_values("Valor_View", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        st.dataframe(
            top10,
            column_config={
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Valor_View": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "Cartao": "Cartão",
            },
            use_container_width=True,
        )
