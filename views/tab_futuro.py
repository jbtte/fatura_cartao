import streamlit as st
import plotly.express as px
import utils
import pandas as pd


def renderizar(df_mes, moeda, largura_grafico):
    st.subheader(
        f"🔮 Raio-X da Dívida ({df_mes['MesAno'].iloc[0] if not df_mes.empty else '--'})"
    )

    if df_mes.empty:
        st.warning("Sem dados neste mês.")
        return

    # Verificação de colunas necessárias
    colunas_necessarias = ["Passivo_View", "TotalParcelas", "ParcelaAtual", "Valor_View"]
    for col in colunas_necessarias:
        if col not in df_mes.columns:
            st.error(f"Coluna '{col}' não encontrada nos dados.")
            return

    # --- NOVOS KPIS FINANCEIROS ---
    # 1. Passivo Total: Quanto de dívida JÁ CONTRAÍDA resta pagar DEPOIS dessa fatura?
    passivo_total = df_mes["Passivo_View"].sum()

    # 2. Parcelas Pagas: Quanto da fatura atual é pagamento de compras antigas/parceladas?
    # Consideramos parcelado tudo que tem TotalParcelas > 1
    pagamento_parcelas = df_mes[df_mes["TotalParcelas"] > 1]["Valor_View"].sum()

    # 3. Novas Compras (Opcional, mas legal para ver o balanço):
    # Tudo que é parcela 1 ou compra à vista (1/1)
    novas_compras = df_mes[df_mes["ParcelaAtual"] == 1]["Valor_View"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Passivo Futuro Total",
        f"{moeda} {passivo_total:,.2f}",
        help="Soma de todas as parcelas que ainda vão vencer nos próximos meses.",
    )

    col2.metric(
        "Pago em Parcelas (Mês)",
        f"{moeda} {pagamento_parcelas:,.2f}",
        help="Valor desta fatura destinado a pagar dívidas de meses anteriores.",
    )

    col3.metric(
        "Novos Gastos (Mês)",
        f"{moeda} {novas_compras:,.2f}",
        help="Compras à vista ou 1ª parcela feitas neste mês.",
    )

    st.markdown("---")

    # --- PROJEÇÃO (Tabela e Gráfico) ---
    st.subheader("Fluxo de Caixa Comprometido")

    df_mes_safe = df_mes.copy()
    df_tabela, df_grafico = utils.processar_dados_futuros(df_mes_safe)

    if df_tabela is not None:
        st.markdown("#### 📝 Detalhamento das Dívidas Ativas")

        df_exibicao = df_tabela.drop(columns=["Data_Final"]).copy()
        df_exibicao.columns = [
            "Item / Loja",
            f"Valor Total ({moeda})",
            f"Valor Parcela ({moeda})",
            "Total Parc.",
            "Parc. Atual",
            "Fim Previsto",
        ]

        st.dataframe(
            df_exibicao.style.format(
                {
                    f"Valor Total ({moeda})": "{:,.2f}",
                    f"Valor Parcela ({moeda})": "{:,.2f}",
                }
            ),
            width=largura_grafico,
        )

        st.markdown("---")

        if not df_grafico.empty:
            fig_proj = px.area(
                df_grafico,
                x="Mês Referência",
                y="Valor",
                title=f"Curva de Desalavancagem ({moeda})",
                labels={
                    "Mês Referência": "Mês de Pagamento",
                    "Valor": "Valor Comprometido",
                },
            )
            st.plotly_chart(fig_proj, width=largura_grafico)
    else:
        st.success("Nenhuma compra parcelada ativa neste mês.")
