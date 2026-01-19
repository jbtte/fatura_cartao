import streamlit as st
import plotly.express as px
import pandas as pd


def renderizar(df_view, meses, moeda, largura_grafico):
    mes_ref = st.selectbox("Selecione o Mês", meses)

    # Importante: .copy() para evitar erros
    df_mes = df_view[df_view["MesAno"] == mes_ref].copy()

    # --- KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Total Gasto ({moeda})", f"{df_mes['Valor_View'].sum():,.2f}")
    c2.metric("Itens", len(df_mes))
    c3.metric(f"Passivo Criado", f"{df_mes['Passivo_View'].sum():,.2f}")

    total = df_mes["Valor_View"].sum()
    essencial = df_mes[df_mes["Tipo_Gasto"] == "Essencial"]["Valor_View"].sum()
    pct = (essencial / total * 100) if total > 0 else 0
    c4.metric("% Essencial", f"{pct:.1f}%")

    st.markdown("---")

    # --- GRÁFICOS PRINCIPAIS ---
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        # VISUALIZAÇÃO HIERÁRQUICA (NOVIDADE TOP)
        st.subheader("Raio-X: Categoria > Subcategoria")
        # O Sunburst mostra hierarquia. Se você clicar em 'Alimentação', ele expande.
        if not df_mes.empty:
            fig_sun = px.sunburst(
                df_mes,
                path=["Categoria", "Subcategoria"],
                values="Valor_View",
                color="Categoria",
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            st.plotly_chart(fig_sun, width=largura_grafico)
        else:
            st.info("Sem dados para exibir hierarquia.")

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
        )
        fig_pareto.update_layout(
            yaxis={"categoryorder": "total ascending"}, showlegend=False
        )
        st.plotly_chart(fig_pareto, width=largura_grafico)

    with col_b2:
        st.caption("Intensidade Semanal")
        df_mes["Data"] = pd.to_datetime(df_mes["Data"])
        df_mes["Dia_Semana"] = df_mes["Data"].dt.day_name()
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
        ordem = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        gastos_dia = (
            df_mes.groupby("Dia_Semana")["Valor_View"]
            .sum()
            .reindex(ordem)
            .reset_index()
        )
        fig_week = px.bar(
            gastos_dia,
            x="Dia_Semana",
            y="Valor_View",
            color_discrete_sequence=["#F1C40F"],
        )
        st.plotly_chart(fig_week, width=largura_grafico)

    # --- DRILL DOWN DETALHADO (FILTRO INTELIGENTE) ---
    st.markdown("---")
    st.subheader("🔬 Microscópio de Gastos")

    # Filtro multiselect
    cats = sorted(df_mes["Categoria"].unique())
    filtro_cats = st.multiselect("Focar em Categorias específicas:", cats)

    # Se o usuário filtrar algo, mostramos a quebra por subcategoria
    if filtro_cats:
        df_focado = df_mes[df_mes["Categoria"].isin(filtro_cats)]

        st.markdown(f"**Detalhamento de: {', '.join(filtro_cats)}**")

        # Gráfico específico de subcategorias do filtro
        fig_sub = px.bar(
            df_focado.groupby("Subcategoria")["Valor_View"]
            .sum()
            .reset_index()
            .sort_values("Valor_View", ascending=False),
            x="Subcategoria",
            y="Valor_View",
            text_auto=".2f",
            title="Onde exatamente foi o dinheiro?",
        )
        st.plotly_chart(fig_sub, width=largura_grafico)

        st.dataframe(
            df_focado[["Data", "Estabelecimento", "Subcategoria", "Valor_View"]],
            width=largura_grafico,
        )
    else:
        st.dataframe(df_mes, width=largura_grafico)
