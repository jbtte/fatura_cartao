import streamlit as st
import plotly.express as px
import utils
import pandas as pd


def renderizar(df_view, meses, largura_grafico):
    st.subheader("⚖️ Duelo de Meses & Médias Históricas")

    # --- SELETORES ---
    c1, c2 = st.columns(2)
    mes_a = c1.selectbox("Mês Referência (A)", meses, index=0)

    opcoes_b = ["Média (Últimos 6 meses)"] + meses
    mes_b = c2.selectbox(
        "Comparar com (B)", opcoes_b, index=1 if len(opcoes_b) > 1 else 0
    )

    st.markdown("---")

    # --- GRÁFICO DE TENDÊNCIA ---
    st.markdown("#### 📈 Análise de Tendência (Últimos 6 Meses)")
    df_hist = utils.buscar_historico_6m(df_view, mes_a)

    if not df_hist.empty:
        df_hist["MesAno"] = df_hist["MesAno"].astype(str)
        df_hist["Média Móvel (3m)"] = (
            df_hist["Valor_View"].rolling(window=3, min_periods=1).mean()
        )
        fig_hist = px.line(
            df_hist,
            x="MesAno",
            y=["Valor_View", "Média Móvel (3m)"],
            markers=True,
            title="Curva de Gastos vs Tendência",
            labels={"value": "Valor (R$)", "MesAno": "Mês", "variable": "Legenda"},
            color_discrete_map={
                "Valor_View": "#2980B9",
                "Média Móvel (3m)": "#E67E22",
            },
        )
        fig_hist.update_layout(hovermode="x unified")
        st.plotly_chart(fig_hist, width=largura_grafico)
    else:
        st.info("Dados históricos insuficientes.")

    st.markdown("---")

    # --- KPIs DE CONTEXTO ---
    if mes_a:
        atual, anterior, media_6m_val = utils.calcular_metricas_contexto(df_view, mes_a)

        st.markdown(f"**Performance do Mês: {mes_a}**")
        k1, k2, k3 = st.columns(3)

        delta_ant = atual - anterior
        k1.metric(
            f"Total {mes_a}",
            f"R$ {atual:,.2f}",
            f"{delta_ant:+,.2f} vs anterior",
            delta_color="inverse",
        )
        k2.metric("Mês Anterior", f"R$ {anterior:,.2f}")

        delta_med = atual - media_6m_val if media_6m_val > 0 else 0
        k3.metric(
            "Média Geral (6m)",
            f"R$ {media_6m_val:,.2f}",
            f"{delta_med:+,.2f} vs média",
            delta_color="inverse",
        )

    st.markdown("---")

    # --- COMPARAÇÃO POR CATEGORIA ---
    if mes_a and mes_b:
        df_a_cat = (
            df_view[df_view["MesAno"] == mes_a]
            .groupby("Categoria")["Valor_View"]
            .sum()
            .reset_index()
        )
        df_a_cat["Origem"] = f"Mês {mes_a}"

        if mes_b == "Média (Últimos 6 meses)":
            df_b_data = utils.gerar_df_media_historica(df_view, mes_a)

            if not df_b_data.empty:
                df_b_plot = df_b_data.copy().rename(columns={"Valor_Media": "Valor_View"})
                df_b_plot["Origem"] = "Média (6m)"
                df_comp_plot = pd.concat([df_a_cat, df_b_plot])

                df_delta = pd.merge(df_a_cat, df_b_data, on="Categoria", how="outer")
                if "Origem" in df_delta.columns:
                    df_delta = df_delta.drop(columns=["Origem"])
                df_delta = df_delta.fillna(0)
                # Positivo = mês A gastou mais que a média (pior)
                df_delta["Diferença"] = df_delta["Valor_View"] - df_delta["Valor_Media"]
                df_delta = df_delta.rename(
                    columns={"Valor_View": f"Valor {mes_a}", "Valor_Media": "Média 6M"}
                )
            else:
                st.warning("Dados insuficientes para calcular média histórica.")
                return
        else:
            df_b_cat = (
                df_view[df_view["MesAno"] == mes_b]
                .groupby("Categoria")["Valor_View"]
                .sum()
                .reset_index()
            )
            df_b_cat["Origem"] = f"Mês {mes_b}"
            df_comp_plot = pd.concat([df_a_cat, df_b_cat])
            df_delta = utils.calcular_delta_meses(df_view, mes_a, mes_b)

        df_comp_plot["Origem"] = df_comp_plot["Origem"].astype(str)

        fig_comp = px.bar(
            df_comp_plot,
            x="Categoria",
            y="Valor_View",
            color="Origem",
            barmode="group",
            title=f"Gastos por Categoria: {mes_a} vs {mes_b}",
            labels={"Valor_View": "R$"},
        )
        st.plotly_chart(fig_comp, width=largura_grafico)

        # --- GRÁFICO DE VARIAÇÕES (mais legível que tabela sozinha) ---
        st.markdown("#### 📊 Maiores Variações por Categoria")
        st.caption("Positivo = mês A gastou mais | Negativo = mês A gastou menos")

        df_delta_reset = df_delta.reset_index() if "Categoria" not in df_delta.columns else df_delta.copy()
        df_delta_sorted = df_delta_reset.sort_values("Diferença")
        df_delta_sorted["Direção"] = df_delta_sorted["Diferença"].apply(
            lambda x: "Aumento" if x > 0 else "Redução"
        )

        fig_delta = px.bar(
            df_delta_sorted,
            x="Diferença",
            y="Categoria",
            orientation="h",
            color="Direção",
            color_discrete_map={"Aumento": "#E74C3C", "Redução": "#27AE60"},
            text_auto=".0f",
            labels={"Diferença": "Variação (R$)"},
        )
        fig_delta.update_layout(showlegend=True, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_delta, width=largura_grafico)

        # --- TABELA DETALHADA ---
        st.markdown("#### 📉 Tabela Detalhada de Variações")

        cols_num = df_delta.select_dtypes(include=["number"]).columns.tolist()
        format_dict = {col: "{:.2f}" for col in cols_num}

        st.dataframe(
            df_delta.sort_values("Diferença", ascending=False)
            .style.format(format_dict)
            .background_gradient(subset=["Diferença"], cmap="RdYlGn_r"),
            width=largura_grafico,
        )
