import streamlit as st
import plotly.express as px
import utils
import pandas as pd


def renderizar(df_mes, largura_grafico):
    st.subheader(
        f"🔮 Raio-X da Dívida ({df_mes['MesAno'].iloc[0] if not df_mes.empty else '--'})"
    )

    if df_mes.empty:
        st.warning("Sem dados neste mês.")
        return

    colunas_necessarias = ["Passivo_View", "TotalParcelas", "ParcelaAtual", "Valor_View"]
    for col in colunas_necessarias:
        if col not in df_mes.columns:
            st.error(f"Coluna '{col}' não encontrada nos dados.")
            return

    passivo_total = df_mes["Passivo_View"].sum()
    pagamento_parcelas = df_mes[df_mes["TotalParcelas"] > 1]["Valor_View"].sum()
    novas_compras = df_mes[df_mes["ParcelaAtual"] == 1]["Valor_View"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Passivo Futuro Total",
        f"R$ {passivo_total:,.2f}",
        help="Soma de todas as parcelas que ainda vão vencer nos próximos meses.",
    )
    col2.metric(
        "Pago em Parcelas (Mês)",
        f"R$ {pagamento_parcelas:,.2f}",
        help="Valor desta fatura destinado a pagar dívidas de meses anteriores.",
    )
    col3.metric(
        "Novos Gastos (Mês)",
        f"R$ {novas_compras:,.2f}",
        help="Compras à vista ou 1ª parcela feitas neste mês.",
    )

    st.markdown("---")

    st.subheader("Fluxo de Caixa Comprometido")

    df_mes_safe = df_mes.copy()
    df_tabela, df_grafico = utils.processar_dados_futuros(df_mes_safe)

    if df_tabela is not None:
        # --- DATA DE QUITAÇÃO ---
        data_livre = df_tabela["Data_Final"].max()
        st.info(f"📅 Livre de todas as parcelas em: **{data_livre.strftime('%m/%Y')}**")

        st.markdown("#### 📝 Detalhamento das Dívidas Ativas")

        df_exibicao = df_tabela.drop(columns=["Data_Final"]).copy()
        df_exibicao.columns = [
            "Item / Loja",
            "Valor Total (R$)",
            "Valor Parcela (R$)",
            "Total Parc.",
            "Parc. Atual",
            "Fim Previsto",
        ]

        st.dataframe(
            df_exibicao.style.format(
                {
                    "Valor Total (R$)": "{:,.2f}",
                    "Valor Parcela (R$)": "{:,.2f}",
                }
            ),
            width=largura_grafico,
        )

        st.markdown("---")

        if not df_grafico.empty:
            # Limita a top 8 itens por valor total; agrupa o restante como "Outros"
            top_itens = (
                df_grafico.groupby("Estabelecimento")["Valor"]
                .sum()
                .nlargest(8)
                .index.tolist()
            )
            df_grafico_plot = df_grafico.copy()
            df_grafico_plot.loc[
                ~df_grafico_plot["Estabelecimento"].isin(top_itens), "Estabelecimento"
            ] = "Outros"
            df_grafico_plot = (
                df_grafico_plot
                .groupby(["Mes_Sort", "Mês Referência", "Estabelecimento"])["Valor"]
                .sum()
                .reset_index()
                .sort_values("Mes_Sort")
            )

            fig_proj = px.area(
                df_grafico_plot,
                x="Mês Referência",
                y="Valor",
                color="Estabelecimento",
                title="Curva de Desalavancagem por Item (R$)",
                labels={
                    "Mês Referência": "Mês de Pagamento",
                    "Valor": "Valor Comprometido (R$)",
                },
            )
            fig_proj.update_layout(hovermode="x unified")
            st.plotly_chart(fig_proj, width=largura_grafico)
    else:
        st.success("Nenhuma compra parcelada ativa neste mês.")
