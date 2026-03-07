# constants.py

# Configurações visuais e financeiras
LARGURA_GRAFICO = "stretch"

# Thresholds de detecção de anomalias
ALERTA_OUTLIER_FATOR = 2.5         # gasto atual > X vezes a média histórica do estabelecimento
ALERTA_ASSINATURA_MIN_MESES = 3    # mínimo de meses para considerar uma cobrança recorrente
ALERTA_ASSINATURA_MAX_CV = 0.15    # coeficiente de variação máximo para considerar valor fixo
ALERTA_ASSINATURA_VARIACAO = 0.10  # variação mínima (%) para alertar mudança de assinatura

# Categorias para classificação (baseado nas categorias reais dos dados)
CATS_ESSENCIAIS = [
    "Alimentação",
    "Saúde",
    "Educação",
    "Transporte",
    "Impostos e Taxas",
    "Impostos e taxas",  # Variação de capitalização nos dados
]
