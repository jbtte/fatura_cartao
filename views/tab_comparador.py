import streamlit as st
import plotly.express as px
import utils
import pandas as pd


def renderizar(df_view, meses, moeda, largura_grafico):
    st.subheader("⚖️ Duelo de Meses & Médias Históricas")

    # --- 1. SELETORES DE CONTEXTO ---
    c1, c2 = st.columns(2)
    mes_a = c1.selectbox("Mês Referência (A)", meses, index=0)

    opcoes_b = ["Média (Últimos 6 meses)"] + meses
    mes_b = c2.selectbox(
        "Comparar com (B)", opcoes_b, index=1 if len(opcoes_b) > 1 else 0
    )

    st.markdown("---")

    # --- 2. GRÁFICO DE TENDÊNCIA (LINHAS + MÉDIA MÓVEL) ---
    st.markdown("#### 📈 Análise de Tendência (Últimos 6 Meses)")
    df_hist = utils.buscar_historico_6m(df_view, mes_a)

    if not df_hist.empty:
        # Garante string para o Eixo X
        df_hist["MesAno"] = df_hist["MesAno"].astype(str)

        # CÁLCULO DA MÉDIA MÓVEL (3 MESES)
        # min_periods=1 garante que a linha comece a ser desenhada já no primeiro ponto
        df_hist["Média Móvel (3m)"] = (
            df_hist["Valor_View"].rolling(window=3, min_periods=1).mean()
        )

        # Plotagem em Linha
        fig_hist = px.line(
            df_hist,
            x="MesAno",
            y=["Valor_View", "Média Móvel (3m)"],
            markers=True,
            title="Curva de Gastos vs Tendência",
            labels={
                "value": f"Valor ({moeda})",
                "MesAno": "Mês",
                "variable": "Legenda",
            },
            color_discrete_map={
                "Valor_View": "#2980B9",
                "Média Móvel (3m)": "#E67E22",
            },  # Azul e Laranja
        )

        # Ajuste visual para limpar o gráfico
        fig_hist.update_layout(
            hovermode="x unified"
        )  # Mostra os dois valores ao passar o mouse

        st.plotly_chart(fig_hist, width=largura_grafico)
    else:
        st.info("Dados históricos insuficientes.")

    st.markdown("---")

    # --- 3. MÉTRICAS DE TENDÊNCIA (KPIs) ---
    if mes_a:
        atual, anterior, media_6m_val = utils.calcular_metricas_contexto(df_view, mes_a)

        st.markdown(f"**Performance do Mês: {mes_a}**")
        k1, k2, k3 = st.columns(3)

        delta_ant = atual - anterior
        k1.metric(
            f"Total {mes_a}",
            f"{moeda} {atual:,.2f}",
            f"{delta_ant:,.2f} vs anterior",
            delta_color="inverse",
        )
        k2.metric("Mês Anterior", f"{moeda} {anterior:,.2f}")

        delta_med = atual - media_6m_val if media_6m_val > 0 else 0
        k3.metric(
            "Média Geral (6m)",
            f"{moeda} {media_6m_val:,.2f}",
            f"{delta_med:,.2f} vs média",
            delta_color="inverse",
        )

    st.markdown("---")

    # --- 4. COMPARAÇÃO DETALHADA POR CATEGORIA ---
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
                df_b_plot = df_b_data.copy().rename(
                    columns={"Valor_Media": "Valor_View"}
                )
                df_b_plot["Origem"] = "Média (6m)"
                df_comp_plot = pd.concat([df_a_cat, df_b_plot])

                df_delta = pd.merge(df_a_cat, df_b_data, on="Categoria", how="outer")

                # Correção de tipos para evitar erro Arrow
                if "Origem" in df_delta.columns:
                    df_delta = df_delta.drop(columns=["Origem"])

                df_delta = df_delta.fillna(0)
                df_delta["Diferença"] = df_delta["Valor_View"] - df_delta["Valor_Media"]
                df_delta = df_delta.rename(
                    columns={"Valor_View": f"Valor {mes_a}", "Valor_Media": "Média 6M"}
                )
            else:
                st.warning("Dados insuficientes para calcular média histórica.")
                df_comp_plot = df_a_cat.copy()
                df_delta = df_a_cat.copy()
                df_delta["Diferença"] = 0
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

        # Correção Arrow: String explícita
        df_comp_plot["Origem"] = df_comp_plot["Origem"].astype(str)

        fig_comp = px.bar(
            df_comp_plot,
            x="Categoria",
            y="Valor_View",
            color="Origem",
            barmode="group",
            title=f"Diferença por Categoria: {mes_a} vs {mes_b}",
        )
        st.plotly_chart(fig_comp, width=largura_grafico)

        # --- 5. TABELA COM FORMATO SEGURO ---
        st.markdown("#### 📉 Tabela Detalhada de Variações")

        cols_num = df_delta.select_dtypes(include=["number"]).columns.tolist()
        format_dict = {col: "{:.2f}" for col in cols_num}

        st.dataframe(
            df_delta.sort_values("Diferença", ascending=False)
            .style.format(format_dict)
            .background_gradient(subset=["Diferença"], cmap="RdYlGn_r"),
            width=largura_grafico,
        )
