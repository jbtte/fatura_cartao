import streamlit as st
import plotly.express as px
import utils
import pandas as pd


def renderizar(df_mes, moeda, largura_grafico):
    st.subheader("Fluxo de Caixa Comprometido")

    # Importante: .copy() aqui também se for manipular
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
                x="Meses_Frente",
                y="Valor",
                title=f"Curva de Desalavancagem ({moeda})",
                labels={
                    "Meses_Frente": "Meses a partir de agora",
                    "Valor": "Valor Comprometido",
                },
            )
            st.plotly_chart(fig_proj, width=largura_grafico)
    else:
        st.success("Nenhuma compra parcelada ativa neste mês.")
