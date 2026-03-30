#!/usr/bin/env python3
"""
parse_pdf.py — Extrai fatura PDF via Gemini API e gera CSV estruturado.

Uso:
    python parse_pdf.py fatura.pdf              # extrai via API e mostra inferidos
    python parse_pdf.py --reclassify 202602     # reclassifica e gera CSV
    python parse_pdf.py --reclassify 202602 --mes-ano 2026-02  # força mês/ano
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("Erro: instale o pacote com: pip install google-genai")
    sys.exit(1)

# Carrega .env se existir
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

CARD_MAP = {
    "2404": "Itau-JP",
    "1400": "Itau-JP",
    "9982": "Itau-JP",
    "4324": "Itau-FA",
    "5732": "Itau-FA",
    "8821": "Rico-JP",
    "6090": "Rico-JP",
}

COLUNAS_CSV = [
    "TxID", "Data", "MesAno", "Estabelecimento", "Categoria", "Subcategoria",
    "Valor_R$", "Cartao", "Observacao", "EhParcela", "ParcelaAtual",
    "TotalParcelas", "ValorTotal", "GrupoParcela", "EhEstorno", "TipodeEstorno",
    "ValorAbsoluto",
]

PROMPT_BASE = """
Você é um extrator de dados de faturas de cartão de crédito brasileiras.

Analise o PDF e retorne APENAS um JSON válido com esta estrutura:

{
  "total_fatura": <float>,
  "mes_ano": "<YYYY-MM do mês de pagamento>",
  "transacoes": [
    {
      "data": "<YYYY-MM-DD>",
      "estabelecimento": "<nome exato como aparece na fatura>",
      "valor_brl": <float, negativo se estorno>,
      "cartao_final": "<4 últimos dígitos do cartão>",
      "parcela_atual": <int, 1 se não parcelado>,
      "total_parcelas": <int, 1 se não parcelado>,
      "eh_estorno": <bool>,
      "categoria_sugerida": "<categoria em português>",
      "subcategoria_sugerida": "<subcategoria em português>"
    }
  ]
}

Regras de extração:
- INCLUIR: todas as compras, encargos, IOF, transações internacionais (valor em R$)
- EXCLUIR: parcelas de "próximas faturas", simulações, limites de crédito
- Parcelas: detectar padrão XX/YY no nome; parcela_atual=XX, total_parcelas=YY
- Estornos: valor_brl negativo e eh_estorno=true
- IOF de transações internacionais: incluir como transação separada com categoria "Impostos e Taxas" e subcategoria "IOF"
- mes_ano: mês de PAGAMENTO da fatura (não da compra)
- Retornar SOMENTE o JSON, sem markdown, sem texto adicional

{categorias}"""


def _build_prompt(regras_path: Path) -> str:
    """Gera o prompt com a seção de categorias derivada do regras.csv atual."""
    from collections import defaultdict
    cats: dict = defaultdict(set)
    if regras_path.exists():
        with open(regras_path, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter=";"):
                cat = row.get("categoria", "").strip()
                sub = row.get("subcategoria", "").strip()
                if cat and sub and cat != "categoria":
                    cats[cat].add(sub)

    if not cats:
        return PROMPT_BASE.replace("{categorias}", "")

    lines = ["Classificação — prefira as categorias e subcategorias abaixo. Só crie novas se nenhuma existente fizer sentido:\n"]
    for cat in sorted(cats):
        subs = ", ".join(sorted(cats[cat]))
        lines.append(f"{cat}: {subs}")

    return PROMPT_BASE.replace("{categorias}", "\n".join(lines))

# ── FUNÇÕES ───────────────────────────────────────────────────────────────────

def gerar_txid(data: str, estab: str, valor: float, cartao: str) -> str:
    base = f"{data}|{estab}|{valor:.2f}|{cartao}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def carregar_regras(path: Path) -> list:
    regras = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            regras.append({
                "palavra_chave": row["palavra_chave"].strip().lower(),
                "categoria": row["categoria"].strip(),
                "subcategoria": row["subcategoria"].strip(),
            })
    # Mais específico (mais longo) primeiro para evitar match genérico antes do específico
    regras.sort(key=lambda r: len(r["palavra_chave"]), reverse=True)
    return regras


def classificar(estabelecimento: str, regras: list) -> tuple:
    """
    Matching em 3 níveis:
      1 — Direto:     keyword é substring do nome do estabelecimento
      2 — Por palavra: palavra do estabelecimento (≥5 chars) é substring de alguma keyword
      3 — Inferido:   nenhum match encontrado

    Retorna (nome_padronizado, categoria, subcategoria, nivel)
    """
    nome_lower = estabelecimento.lower()

    # Nível 1: match direto
    for regra in regras:
        if regra["palavra_chave"] in nome_lower:
            return regra["palavra_chave"].title(), regra["categoria"], regra["subcategoria"], 1

    # Nível 2: match por palavra (palavras ≥5 chars para evitar falsos positivos)
    palavras = [p for p in re.split(r"[\s\*\.\-\/]+", nome_lower) if len(p) >= 5]
    for palavra in palavras:
        for regra in regras:
            if palavra in regra["palavra_chave"]:
                return regra["palavra_chave"].title(), regra["categoria"], regra["subcategoria"], 2

    # Nível 3: inferido
    return estabelecimento, "", "", 3


def extrair_via_gemini(pdf_path: Path, api_key: str, regras_path: Path) -> dict:
    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(regras_path)

    print(f"📤 Enviando {pdf_path.name} para Gemini API...")
    with open(pdf_path, "rb") as f:
        uploaded = client.files.upload(
            file=f,
            config=genai_types.UploadFileConfig(
                mime_type="application/pdf",
                display_name=pdf_path.name,
            ),
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[uploaded, prompt],
    )

    text = response.text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"\nErro ao interpretar JSON do Gemini: {e}")
        print("Resposta recebida:\n", text[:500])
        sys.exit(1)


def formatar_br(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


def processar(dados: dict, regras: list, mes_ano: str) -> tuple:
    """Retorna (linhas_csv, inferidos, contadores_nivel)."""
    linhas = []
    inferidos = []
    vistos = {}
    contadores = {1: 0, 2: 0, 3: 0}

    for tx in dados.get("transacoes", []):
        estab_original = str(tx.get("estabelecimento", "")).strip()
        # Remove padrão XX/YY do nome para não poluir o estabelecimento
        estab_limpo = re.sub(r"\s*\d{1,2}/\d{1,2}\s*$", "", estab_original).strip()

        valor = float(tx.get("valor_brl", 0))
        cartao_final = str(tx.get("cartao_final", "")).strip().zfill(4)
        cartao = CARD_MAP.get(cartao_final, f"Desconhecido-{cartao_final}")

        parcela_atual = max(1, int(tx.get("parcela_atual", 1) or 1))
        total_parcelas = max(1, int(tx.get("total_parcelas", 1) or 1))
        eh_parcela = 1 if total_parcelas > 1 else 0
        eh_estorno = 1 if tx.get("eh_estorno", False) else 0
        valor_absoluto = abs(valor)
        valor_total = valor_absoluto * total_parcelas
        data_iso = str(tx.get("data", ""))

        nome_pad, categoria, subcategoria, nivel = classificar(estab_limpo, regras)
        contadores[nivel] += 1

        if nivel == 3:
            categoria = str(tx.get("categoria_sugerida", "")).strip()
            subcategoria = str(tx.get("subcategoria_sugerida", "")).strip()
            nome_pad = estab_limpo
            chave = estab_limpo.lower()
            if chave not in vistos:
                vistos[chave] = True
                inferidos.append({
                    "palavra_chave": chave,
                    "categoria": categoria,
                    "subcategoria": subcategoria,
                })

        tid = gerar_txid(data_iso, nome_pad, valor_absoluto, cartao)

        linhas.append({
            "TxID": tid,
            "Data": data_iso,
            "MesAno": mes_ano,
            "Estabelecimento": nome_pad,
            "Categoria": categoria,
            "Subcategoria": subcategoria,
            "Valor_R$": formatar_br(valor),
            "Cartao": cartao,
            "Observacao": str(tx.get("observacao", "")),
            "EhParcela": eh_parcela,
            "ParcelaAtual": parcela_atual,
            "TotalParcelas": total_parcelas,
            "ValorTotal": formatar_br(valor_total),
            "GrupoParcela": nome_pad,
            "EhEstorno": eh_estorno,
            "TipodeEstorno": "Geral" if eh_estorno else "",
            "ValorAbsoluto": formatar_br(valor_absoluto),
        })

    return linhas, inferidos, contadores


def salvar_csv(linhas: list, caminho: Path):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CSV, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(linhas)


def reconciliar(linhas: list, total_fatura: float):
    total_csv = sum(float(l["Valor_R$"].replace(",", ".")) for l in linhas)
    diff = abs(total_csv - total_fatura)
    ok = diff <= 0.02
    status = "✓" if ok else "✗"
    print(f"\n📊 Reconciliação:")
    print(f"   Total da fatura (PDF):  R$ {total_fatura:>10,.2f}")
    print(f"   Total calculado (CSV):  R$ {total_csv:>10,.2f}")
    print(f"   Diferença:              R$ {diff:>10.2f}  {status}")
    if not ok:
        print("   ⚠  Diferença acima de R$ 0,02 — verifique encargos ou IOF omitidos")


def imprimir_resultado(inferidos: list, contadores: dict):
    total = sum(contadores.values())
    print(f"\n📋 Classificação ({total} transações):")
    print(f"   Nível 1 — match direto:      {contadores[1]:>3}")
    print(f"   Nível 2 — match por palavra: {contadores[2]:>3}")
    print(f"   Nível 3 — inferido (Gemini): {contadores[3]:>3}")

    if not inferidos:
        print("\n✅ Nenhum item inferido — todas as transações foram classificadas pelo regras.csv")
        return

    print(f"\n⚠  {len(inferidos)} item(ns) inferido(s) pelo Gemini.")
    print("   Revise, corrija se necessário e adicione ao regras.csv:\n")
    print("palavra_chave,categoria,subcategoria")
    for item in inferidos:
        print(f'{item["palavra_chave"]},{item["categoria"]},{item["subcategoria"]}')


# ── COMANDOS ──────────────────────────────────────────────────────────────────

def cmd_extrair(args, projeto_root: Path):
    """Chama Gemini API, salva JSON bruto e imprime inferidos. Não gera CSV."""
    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        print(f"Erro: arquivo não encontrado: {pdf_path}")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Erro: GEMINI_API_KEY não definida em .env ou no ambiente")
        sys.exit(1)

    raw_dir = projeto_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    regras_path = projeto_root / "data" / "regras.csv"
    regras = carregar_regras(regras_path)

    dados = extrair_via_gemini(pdf_path, api_key, regras_path)

    mes_ano = args.mes_ano or dados.get("mes_ano", "")
    if not mes_ano:
        print("⚠  Mês/ano não detectado. Use --mes-ano YYYY-MM.")

    # Salva JSON bruto para reclassify posterior (sem custo de API)
    json_path = raw_dir / f"{mes_ano.replace('-', '')}_raw.json"
    json_path.write_text(json.dumps(dados, ensure_ascii=False, indent=2))
    print(f"💾 JSON salvo em {json_path.relative_to(projeto_root)}")

    linhas, inferidos, contadores = processar(dados, regras, mes_ano)
    reconciliar(linhas, float(dados.get("total_fatura", 0)))
    imprimir_resultado(inferidos, contadores)

    if inferidos:
        print(f"\n💡 Após atualizar regras.csv, rode:")
        print(f"   python parse_pdf.py --reclassify {mes_ano.replace('-', '')}")


def cmd_reclassify(args, projeto_root: Path):
    """Lê JSON bruto, aplica regras.csv atualizado e gera CSV."""
    raw_dir = projeto_root / "data" / "raw"
    json_path = raw_dir / f"{args.reclassify}_raw.json"

    if not json_path.exists():
        print(f"Erro: {json_path.name} não encontrado.")
        print(f"      Rode primeiro: python parse_pdf.py fatura.pdf")
        sys.exit(1)

    regras = carregar_regras(projeto_root / "data" / "regras.csv")
    dados = json.loads(json_path.read_text())
    mes_ano = args.mes_ano or dados.get("mes_ano", "")

    linhas, inferidos, contadores = processar(dados, regras, mes_ano)
    reconciliar(linhas, float(dados.get("total_fatura", 0)))
    imprimir_resultado(inferidos, contadores)

    if inferidos:
        resp = input(f"\n⚠  Ainda há {len(inferidos)} inferido(s). Gerar CSV com categoria 'Diversos'? (s/N): ").strip().lower()
        if resp != "s":
            print("Cancelado. Atualize o regras.csv e rode novamente.")
            sys.exit(0)
        nomes_inferidos = {item["palavra_chave"] for item in inferidos}
        for linha in linhas:
            if linha["Estabelecimento"].lower() in nomes_inferidos:
                linha["Categoria"] = "Diversos"
                linha["Subcategoria"] = "Diversos"

    csv_path = raw_dir / f"{args.reclassify}.csv"
    if csv_path.exists():
        resp = input(f"\n⚠  {csv_path.name} já existe. Sobrescrever? (s/N): ").strip().lower()
        if resp != "s":
            print("Cancelado.")
            sys.exit(0)

    salvar_csv(linhas, csv_path)
    print(f"\n✅ {len(linhas)} transações salvas em {csv_path.relative_to(projeto_root)}")

    pi_dest = "jbtte@raspberrypi.local:/home/jbtte/fatura_cartao/data/raw/"
    print(f"\n📡 Enviando para Pi ({pi_dest})...")
    ret = os.system(f'scp "{csv_path}" {pi_dest}')
    if ret == 0:
        print("✅ CSV enviado ao Pi com sucesso.")
        json_path.unlink()
        print(f"🗑  {json_path.name} removido.")
    else:
        print("⚠  Falha ao enviar via scp. CSV local preservado em:", csv_path)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extrai fatura PDF via Gemini API e gera CSV estruturado.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python parse_pdf.py fatura.pdf\n"
            "  python parse_pdf.py --reclassify 202602\n"
            "  python parse_pdf.py --reclassify 202602 --mes-ano 2026-02\n"
        ),
    )
    parser.add_argument("pdf", nargs="?", help="Caminho para o PDF da fatura")
    parser.add_argument("--reclassify", metavar="YYYYMM", help="Reclassifica JSON salvo e gera CSV")
    parser.add_argument("--mes-ano", help="Forçar mês/ano no formato YYYY-MM")
    args = parser.parse_args()

    projeto_root = Path(__file__).parent

    if args.reclassify:
        cmd_reclassify(args, projeto_root)
    elif args.pdf:
        cmd_extrair(args, projeto_root)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
