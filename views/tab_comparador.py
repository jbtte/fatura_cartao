import streamlit as st
import plotly.express as px
import utils


def renderizar(df_view, meses, largura_grafico):
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
        st.plotly_chart(fig_comp, width=largura_grafico)

        st.markdown("#### Detalhe da Variação")
        df_delta = utils.calcular_delta_meses(df_view, mes_a, mes_b)
        st.dataframe(df_delta.style.format("{:.2f}"), width=largura_grafico)
