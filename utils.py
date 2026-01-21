import pandas as pd
import glob
import os
import streamlit as st
import re
import numpy as np
from constants import CATS_ESSENCIAIS


# --- FUNÇÕES AUXILIARES DE LIMPEZA (fora do cache para melhor performance) ---


def _limpar_valor(val):
    """Converte valores monetários para float, tratando formatos BR e internacional."""
    # Se já for numérico válido, retorna diretamente
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return 0.0
        return float(val)

    val = str(val).strip()
    if not val or val.lower() == "nan":
        return 0.0

    if "R$" in val:
        val = val.replace("R$", "").strip()

    # Formato brasileiro: 1.234,56 (ponto como milhar, vírgula como decimal)
    # Formato internacional: 1,234.56 (vírgula como milhar, ponto como decimal)
    if val.count(".") >= 1 and val.count(",") == 1:
        # Provavelmente formato brasileiro: 1.234,56
        val = val.replace(".", "").replace(",", ".")
    elif val.count(",") >= 1 and val.count(".") == 0:
        # Só tem vírgula: 1234,56
        val = val.replace(",", ".")

    return pd.to_numeric(val, errors="coerce")


def _limpar_total_parcelas(val):
    """Extrai o total de parcelas. Ex: '01/10' -> 10, 12.0 -> 12."""
    # Se já for numérico válido, retorna diretamente
    try:
        num_val = float(val)
        if not pd.isna(num_val) and num_val >= 1 and float(num_val).is_integer():
            return int(num_val)
    except (ValueError, TypeError):
        pass

    s = str(val).strip()
    if not s or s.lower() == "nan":
        return 1

    # Proteção contra Dinheiro: Se tiver vírgula e não for inteiro (ex: 12,50), rejeita.
    s_clean = s.replace(",", ".")
    try:
        f_val = float(s_clean)
        if f_val.is_integer() and f_val >= 1:
            return int(f_val)
        if not f_val.is_integer():
            return 1  # É centavo (12.50), ignora
    except ValueError:
        pass

    # Lógica da Barra: "01/10" ou "1 de 10"
    numeros = re.findall(r"(\d+)", s)
    if not numeros:
        return 1

    # Para o TOTAL, queremos o último número (o denominador)
    return int(numeros[-1])


def _limpar_parcela_atual(val):
    """Extrai a parcela atual. Ex: '01/10' -> 1, 3.0 -> 3."""
    # Se já for numérico válido, retorna diretamente
    try:
        num_val = float(val)
        if not pd.isna(num_val) and num_val >= 1 and float(num_val).is_integer():
            return int(num_val)
    except (ValueError, TypeError):
        pass

    s = str(val).strip()
    numeros = re.findall(r"(\d+)", s)
    return int(numeros[0]) if numeros else 1


@st.cache_data
def carregar_dados():
    caminho = os.path.join("data", "raw", "*.csv")
    arquivos = glob.glob(caminho)

    if not arquivos:
        return None

    lista_dfs = []

    for f in arquivos:
        try:
            df_temp = pd.read_csv(f, encoding="utf-8")
            df_temp.columns = [c.strip() for c in df_temp.columns]

            # --- DETECÇÃO DE SHIFT (ARQUIVO TORTO) ---
            if "MesAno" in df_temp.columns:
                col_mes = df_temp["MesAno"].astype(str)
                linhas_invalidas = ~col_mes.str.match(r"^\d{4}-\d{2}$")

                if linhas_invalidas.mean() > 0.5:
                    # SHIFT ESQUERDA DETECTADO: Recuperando colunas deslocadas

                    real_valor = df_temp["Subcategoria"].copy()

                    # AQUI ESTÁ A CHAVE: Recuperar o 'EhParcela' real
                    # Se houve deslocamento, 'EhParcela' caiu na coluna anterior ('Observacao')
                    if "Observacao" in df_temp.columns:
                        real_eh_parcela = df_temp["Observacao"].copy()
                    else:
                        real_eh_parcela = 0  # Fallback

                    # Recupera números das parcelas
                    real_total_parc = df_temp["ParcelaAtual"].copy()
                    real_curr_parc = df_temp["EhParcela"].copy()

                    # Aplica Correção
                    df_temp["MesAno"] = np.nan
                    df_temp["Valor_R$"] = real_valor
                    df_temp["EhParcela"] = real_eh_parcela  # Salva o árbitro correto
                    df_temp["TotalParcelas"] = pd.to_numeric(
                        real_total_parc, errors="coerce"
                    )
                    df_temp["ParcelaAtual"] = pd.to_numeric(
                        real_curr_parc, errors="coerce"
                    )

            lista_dfs.append(df_temp)

        except Exception as e:
            st.warning(f"Erro ao ler {os.path.basename(f)}: {e}")
            continue

    if not lista_dfs:
        return None

    df = pd.concat(lista_dfs, ignore_index=True)

    # --- 1. LIMPEZA DE DADOS ---
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])

    # MesAno
    if "MesAno" in df.columns:
        df["MesAno"] = df["MesAno"].astype(str).str.strip()
        mask_invalido = ~df["MesAno"].str.match(r"^\d{4}-\d{2}$")
        mask_nulo = (
            (df["MesAno"] == "") | (df["MesAno"].str.lower() == "nan") | mask_invalido
        )
        df.loc[mask_nulo, "MesAno"] = df.loc[mask_nulo, "Data"].dt.strftime("%Y-%m")
    else:
        df["MesAno"] = df["Data"].dt.strftime("%Y-%m")

    # Textos
    for col in ["Estabelecimento", "Categoria", "Subcategoria"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # Valores (usa função externa para melhor performance com cache)
    df["Valor_R$"] = df["Valor_R$"].apply(_limpar_valor).fillna(0.0)

    # --- 2. LÓGICA DO ÁRBITRO "EH PARCELA" ---

    # Garante que EhParcela seja 0 ou 1
    if "EhParcela" in df.columns:
        # Converte tudo para numérico, erros viram 0 (Não)
        df["EhParcela"] = (
            pd.to_numeric(df["EhParcela"], errors="coerce").fillna(0).astype(int)
        )
    else:
        df["EhParcela"] = 0

    # --- EXTRAÇÃO ROBUSTA DE PARCELAS (usa funções externas) ---
    df["ParcelaAtual"] = df["ParcelaAtual"].apply(_limpar_parcela_atual).astype(int)
    df["TotalParcelas"] = df["TotalParcelas"].apply(_limpar_total_parcelas).astype(int)

    # Trava de Segurança Extra (Mantida)
    mask_erro = (df["TotalParcelas"] > 60) | (df["TotalParcelas"] < 1)
    df.loc[mask_erro, "TotalParcelas"] = 1
    df.loc[mask_erro, "ParcelaAtual"] = 1

    # --- CORREÇÃO: Sincronização de Parcelas ---
    # Se TotalParcelas > 1, garante que a flag EhParcela seja 1 (Verdadeiro)
    df.loc[df["TotalParcelas"] > 1, "EhParcela"] = 1

    # --- 3. CÁLCULO DE PASSIVO BLINDADO ---
    # Só calcula passivo SE EhParcela for 1 (Verdadeiro)
    # np.where(CONDIÇÃO, VALOR_SE_SIM, VALOR_SE_NAO)
    df["Passivo_Futuro"] = np.where(
        df["EhParcela"] == 1,
        (df["TotalParcelas"] - df["ParcelaAtual"]) * df["Valor_R$"],
        0.0,  # Se não for parcela, dívida futura é ZERO
    )

    df["Passivo_Futuro"] = df["Passivo_Futuro"].clip(lower=0)

    # Categorias
    if "Categoria" in df.columns:
        df["Tipo_Gasto"] = df["Categoria"].apply(
            lambda x: "Essencial" if x in CATS_ESSENCIAIS else "Estilo de Vida"
        )
    else:
        df["Tipo_Gasto"] = "Indefinido"

    return df


# --- FUNÇÕES DE VISUALIZAÇÃO ---


def aplicar_conversao_moeda(df, simular_usd, taxa):
    df_view = df.copy()
    fator = 1 / taxa if simular_usd else 1
    df_view["Valor_View"] = df_view["Valor_R$"] * fator
    if "Passivo_Futuro" in df_view.columns:
        df_view["Passivo_View"] = df_view["Passivo_Futuro"] * fator
    else:
        df_view["Passivo_View"] = 0.0
    return df_view, "USD" if simular_usd else "BRL"


def calcular_delta_meses(df, mes_a, mes_b):
    resumo_a = df[df["MesAno"] == mes_a].groupby("Categoria")["Valor_View"].sum()
    resumo_b = df[df["MesAno"] == mes_b].groupby("Categoria")["Valor_View"].sum()
    df_delta = pd.DataFrame(
        {f"Valor {mes_a}": resumo_a, f"Valor {mes_b}": resumo_b}
    ).fillna(0)
    df_delta["Diferença"] = df_delta[f"Valor {mes_b}"] - df_delta[f"Valor {mes_a}"]
    return df_delta.sort_values("Diferença", ascending=False)


def processar_dados_futuros(df_mes):
    if df_mes.empty:
        return None, None

    # FILTRO DUPLO: Só é ativo se (Total > 1) E (EhParcela == 1)
    ativos = df_mes[
        (df_mes["TotalParcelas"] > 1)
        & (df_mes["ParcelaAtual"] < df_mes["TotalParcelas"])
        & (df_mes["EhParcela"] == 1)  # O Juiz entra em ação aqui também
    ].copy()

    if ativos.empty:
        return None, None

    try:
        data_base = pd.to_datetime(df_mes["MesAno"].iloc[0] + "-01")
    except (ValueError, IndexError, KeyError):
        data_base = pd.Timestamp.now().normalize()

    ativos["Valor_Total_Compra"] = ativos["Valor_View"] * ativos["TotalParcelas"]
    ativos["Meses_Restantes"] = ativos["TotalParcelas"] - ativos["ParcelaAtual"]

    ativos["Data_Final"] = ativos.apply(
        lambda x: data_base + pd.DateOffset(months=int(x["Meses_Restantes"])), axis=1
    )
    ativos["Ultima_Parcela_Fmt"] = ativos["Data_Final"].dt.strftime("%m/%Y")

    df_tabela = ativos[
        [
            "Estabelecimento",
            "Valor_Total_Compra",
            "Valor_View",
            "TotalParcelas",
            "ParcelaAtual",
            "Ultima_Parcela_Fmt",
            "Data_Final",
        ]
    ].sort_values(by=["Data_Final", "Valor_View"], ascending=[False, False])

    projecao = []
    for _, row in ativos.iterrows():
        faltam = int(row["Meses_Restantes"])
        for i in range(1, faltam + 1):
            data_futura = data_base + pd.DateOffset(months=i)
            projecao.append(
                {
                    "Mes_Sort": data_futura.strftime("%Y-%m"),
                    "Mês Referência": data_futura.strftime("%m/%Y"),
                    "Valor": row["Valor_View"],
                }
            )

    if projecao:
        df_grafico = (
            pd.DataFrame(projecao)
            .groupby(["Mes_Sort", "Mês Referência"])["Valor"]
            .sum()
            .reset_index()
            .sort_values("Mes_Sort")
        )
    else:
        df_grafico = pd.DataFrame()

    return df_tabela, df_grafico


def calcular_metricas_contexto(df, mes_ref):
    df_totais = (
        df.groupby("MesAno")["Valor_View"].sum().reset_index().sort_values("MesAno")
    )
    # Reset index para garantir que iloc e index sejam consistentes
    df_totais = df_totais.reset_index(drop=True)

    meses_lista = df_totais["MesAno"].tolist()
    if mes_ref not in meses_lista:
        return 0.0, 0.0, 0.0

    pos = meses_lista.index(mes_ref)
    val_atual = df_totais.loc[pos, "Valor_View"]
    val_anterior = df_totais.loc[pos - 1, "Valor_View"] if pos > 0 else 0.0
    inicio = max(0, pos - 6)
    media_6m = df_totais.iloc[inicio:pos]["Valor_View"].mean() if pos > 0 else 0.0
    return val_atual, val_anterior, media_6m


def buscar_historico_6m(df_view, mes_ref):
    df_totais = (
        df_view.groupby("MesAno")["Valor_View"]
        .sum()
        .reset_index()
        .sort_values("MesAno")
    )
    meses_lista = df_totais["MesAno"].tolist()
    if mes_ref not in meses_lista:
        return pd.DataFrame()
    idx = meses_lista.index(mes_ref)
    inicio = max(0, idx - 5)
    return df_totais.iloc[inicio : idx + 1]


def gerar_df_media_historica(df_view, mes_ref, meses_janela=6):
    df_totais = df_view.sort_values("MesAno")
    meses_lista = sorted(df_view["MesAno"].unique())
    if mes_ref not in meses_lista:
        return pd.DataFrame()
    idx = meses_lista.index(mes_ref)
    inicio = max(0, idx - meses_janela)
    meses_analise = meses_lista[inicio:idx]
    if not meses_analise:
        return pd.DataFrame()
    df_janela = df_view[df_view["MesAno"].isin(meses_analise)]
    df_media = df_janela.groupby("Categoria")["Valor_View"].sum() / len(meses_analise)
    return df_media.reset_index().rename(columns={"Valor_View": "Valor_Media"})
