import streamlit as st
import pandas as pd
import utils


def renderizar(df, mes_ref, largura_grafico):
    st.subheader(f"⚠️ Alertas & Anomalias — {mes_ref}")

    alertas = utils.detectar_anomalias(df, mes_ref)

    if not alertas:
        st.info("Dados insuficientes para análise.")
        return

    outliers = alertas.get("outliers", [])
    assinaturas = alertas.get("assinaturas", [])
    duplicatas = alertas.get("duplicatas", [])
    sem_cat = alertas.get("sem_categoria", [])

    total = len(outliers) + len(assinaturas) + len(duplicatas) + len(sem_cat)

    if total == 0:
        st.success("Nenhuma anomalia detectada neste mês.")
        return

    # --- RESUMO ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gastos fora do padrão", len(outliers))
    c2.metric("Assinaturas alteradas", len(assinaturas))
    c3.metric("Possíveis duplicatas", len(duplicatas))
    c4.metric("Sem classificação", len(sem_cat))

    st.markdown("---")

    # --- OUTLIERS ---
    if outliers:
        st.markdown("### 🔴 Gastos fora do padrão")
        st.caption("Valor atual acima de 2.5× a média histórica do estabelecimento (mín. 2 ocorrências anteriores)")
        df_out = pd.DataFrame(outliers)
        st.dataframe(
            df_out.style.format({
                "Valor Atual (R$)": "R$ {:.2f}",
                "Média Histórica (R$)": "R$ {:.2f}",
                "Vezes acima": "{:.1f}×",
            }).background_gradient(subset=["Vezes acima"], cmap="Reds"),
            use_container_width=True,
        )
        st.markdown("")

    # --- ASSINATURAS ---
    if assinaturas:
        st.markdown("### 🟡 Assinaturas com valor alterado")
        st.caption("Cobrança recorrente (≥3 meses) com variação superior a 10% do valor habitual")
        df_ass = pd.DataFrame(assinaturas)
        def cor_variacao(val):
            color = "#E74C3C" if val > 0 else "#27AE60"
            return f"color: {color}; font-weight: bold"
        st.dataframe(
            df_ass.style.format({
                "Valor Atual (R$)": "R$ {:.2f}",
                "Valor Habitual (R$)": "R$ {:.2f}",
                "Variação (%)": "{:+.1f}%",
            }).applymap(cor_variacao, subset=["Variação (%)"]),
            use_container_width=True,
        )
        st.markdown("")

    # --- DUPLICATAS ---
    if duplicatas:
        st.markdown("### 🟠 Possíveis duplicatas")
        st.caption("⚠️ Forte = mesmo estabelecimento, valor e data. ℹ️ Fraco = mesmo estabelecimento e valor em datas distintas")
        df_dup = pd.DataFrame(duplicatas)
        st.dataframe(
            df_dup.style.format({"Valor (R$)": "R$ {:.2f}"}),
            use_container_width=True,
        )
        st.markdown("")

    # --- SEM CATEGORIA ---
    if sem_cat:
        st.markdown("### ⚪ Sem classificação")
        st.caption("Transações categorizadas como 'Diversos/Diversos' — estabelecimento não reconhecido pelo regras.csv")
        df_sc = pd.DataFrame(sem_cat)
        st.dataframe(
            df_sc.style.format({"Valor (R$)": "R$ {:.2f}"}),
            use_container_width=True,
        )
