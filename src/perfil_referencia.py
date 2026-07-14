# Perfil de referência do demo — calibrado em ordem de grandeza a um player real
# (Nu Holdings / Nubank, Form 20-F FY2025) e usado como default do dashboard (ADR-0009).
#
# ⚠️ Honestidade de dados: Nubank é BANCO — balanço dominado por depósitos/carteira, não
# por caixa operacional pagando fornecedor no exterior. Usamos só como ÂNCORA DE ESCALA.
# Cada campo é rotulado como (REAL, com fonte) ou (ILUSTRATIVO, premissa do demo).

# --- (REAL) Nu Holdings FY2025, Form 20-F protocolado na SEC em 25/02/2026 ---
NUBANK_FY2025 = {
    "receita_total_usd_bi": 15.8,          # +37% a/a
    "lucro_liquido_usd_bi": 2.9,
    "caixa_equivalentes_holding_usd_bi": 3.0,  # ~US$3,0 bi (Dec/2025)
    "depositos_totais_usd_bi": 41.9,
    "carteira_rende_juros_usd_bi": 18.5,
    "clientes_milhoes": 131,
    "fonte": "https://www.sec.gov/Archives/edgar/data/1691493/000129281426002166/nuform20f_2025.htm",
}

# --- (ILUSTRATIVO) tesouraria operacional sintética de uma fintech BR nessa escala ---
# Escolhida como subconjunto conservador da liquidez de holding (~US$3bi ≈ R$16,5bi):
# um caixa operacional na casa de centenas de milhões de BRL é plausível e defensável.
PERFIL_DEMO = {
    "saldo_brl": 500_000_000,              # R$ 500 mi — caixa operacional (ILUSTRATIVO)
    "saldo_usd": 30_000_000,               # posição em dólar (ILUSTRATIVO)
    "saldo_usdt": 10_000_000,              # working capital já no trilho (ILUSTRATIVO)
    "previsao_gasto_brl_30d": 150_000_000,   # opex mensal (ILUSTRATIVO)
    "previsao_recebimento_usd_30d": 20_000_000,  # receita em USD (ILUSTRATIVO)
    "previsao_pagamento_usd_30d": 200_000_000 / 5.5,  # ~US$36 mi de pagamento cross-border 30d (ILUSTRATIVO)
}