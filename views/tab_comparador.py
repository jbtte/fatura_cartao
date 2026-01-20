import streamlit as st
import plotly.express as px
import utils
import pandas as pd


def renderizar(df_view, meses, moeda, largura_grafico):
    st.subheader("⚖️ Duelo de Meses & Médias Históricas")

    # --- 1. SELETORES DE CONTEXTO ---
    c1, c2 = st.columns(2)
    # Mês A é a nossa âncora para o histórico e comparação
    mes_a = c1.selectbox("Mês Referência (A)", meses, index=0)

    # Opção dinâmica para comparar com outro mês ou com a média
    opcoes_b = ["Média (Últimos 6 meses)"] + meses
    mes_b = c2.selectbox(
        "Comparar com (B)", opcoes_b, index=1 if len(opcoes_b) > 1 else 0
    )

    st.markdown("---")

    # --- 2. GRÁFICO DE EVOLUÇÃO (TENDÊNCIA 6 MESES) ---
    # Este gráfico dá a visão macro antes do detalhamento por categoria
    st.markdown("#### 📈 Evolução do Gasto Total (Últimos 6 Meses)")
    df_hist = utils.buscar_historico_6m(df_view, mes_a)

    if not df_hist.empty:
        fig_hist = px.bar(
            df_hist,
            x="MesAno",
            y="Valor_View",
            text_auto=".0f",
            color_discrete_sequence=["#34495E"],
            labels={"MesAno": "Mês", "Valor_View": f"Total ({moeda})"},
        )

        # Linha de média para referência visual rápida no histórico
        media_valor = df_hist["Valor_View"].mean()
        fig_hist.add_hline(
            y=media_valor,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Média: {media_valor:,.0f}",
        )
        st.plotly_chart(fig_hist, width=largura_grafico)
    else:
        st.info("Dados históricos insuficientes para mostrar a evolução de 6 meses.")

    st.markdown("---")

    # --- 3. MÉTRICAS DE TENDÊNCIA (KPIs) ---
    if mes_a:
        atual, anterior, media_6m_val = utils.calcular_metricas_contexto(df_view, mes_a)

        st.markdown(f"**Análise de Desempenho: {mes_a}**")
        k1, k2, k3 = st.columns(3)

        # Comparação com o mês imediatamente anterior
        delta_ant = atual - anterior
        k1.metric(
            f"Total {mes_a}",
            f"{moeda} {atual:,.2f}",
            f"{delta_ant:,.2f} vs anterior",
            delta_color="inverse",
        )

        # Valor do mês anterior para referência
        k2.metric("Mês Anterior", f"{moeda} {anterior:,.2f}")

        # Comparação com a média histórica (6 meses)
        delta_med = atual - media_6m_val if media_6m_val > 0 else 0
        k3.metric(
            "Média (6m)",
            f"{moeda} {media_6m_val:,.2f}",
            f"{delta_med:,.2f} vs média",
            delta_color="inverse",
        )

    st.markdown("---")

    # --- 4. COMPARAÇÃO DETALHADA POR CATEGORIA ---
    if mes_a and mes_b:
        # Lógica para Mês A (Sempre fixo)
        df_a_cat = (
            df_view[df_view["MesAno"] == mes_a]
            .groupby("Categoria")["Valor_View"]
            .sum()
            .reset_index()
        )
        df_a_cat["Origem"] = f"Mês {mes_a}"

        if mes_b == "Média (Últimos 6 meses)":
            # Comparação: Mês Selecionado vs Média Virtual
            df_b_data = utils.gerar_df_media_historica(df_view, mes_a)

            if not df_b_data.empty:
                # Prepara dados para o gráfico
                df_b_plot = df_b_data.copy().rename(
                    columns={"Valor_Media": "Valor_View"}
                )
                df_b_plot["Origem"] = "Média (6m)"
                df_comp_plot = pd.concat([df_a_cat, df_b_plot])

                # Prepara dados para a tabela Delta
                df_delta = pd.merge(
                    df_a_cat, df_b_data, on="Categoria", how="outer"
                ).fillna(0)
                df_delta["Diferença"] = df_delta["Valor_View"] - df_delta["Valor_Media"]
                df_delta = df_delta.rename(
                    columns={"Valor_View": f"Valor {mes_a}", "Valor_Media": "Média 6M"}
                )
            else:
                st.warning("Não há meses anteriores suficientes para calcular a média.")
                return
        else:
            # Comparação: Mês A vs Mês B (Mês real)
            df_b_cat = (
                df_view[df_view["MesAno"] == mes_b]
                .groupby("Categoria")["Valor_View"]
                .sum()
                .reset_index()
            )
            df_b_cat["Origem"] = f"Mês {mes_b}"
            df_comp_plot = pd.concat([df_a_cat, df_b_cat])

            # Tabela Delta entre dois meses reais
            df_delta = utils.calcular_delta_meses(df_view, mes_a, mes_b)

        # Renderização do Gráfico de Barras Agrupadas
        fig_comp = px.bar(
            df_comp_plot,
            x="Categoria",
            y="Valor_View",
            color="Origem",
            barmode="group",
            title=f"Diferença por Categoria: {mes_a} vs {mes_b}",
        )
        st.plotly_chart(fig_comp, width=largura_grafico)

        # Renderização da Tabela com Mapa de Calor (Heatmap)
        st.markdown("#### 📉 Tabela Detalhada de Variações")
        st.dataframe(
            df_delta.sort_values("Diferença", ascending=False)
            .style.format("{:.2f}")
            .background_gradient(
                subset=["Diferença"], cmap="RdYlGn_r"
            ),  # Verde para queda, Vermelho para alta
            width=largura_grafico,
        )
