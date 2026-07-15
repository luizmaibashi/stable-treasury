# Perfil de referência do demo — calibrado em ordem de grandeza a um player real com
# EXPOSIÇÃO CAMBIAL ESTRUTURAL: Azul S.A. (aérea brasileira), Form 20-F FY2024 (ADR-0011 #5).
#
# Por que aérea (e não banco): passivo pesado em USD (leasing de aeronaves, combustível,
# manutenção, dívida) contra receita majoritariamente em BRL. É o caso de LIVRO-TEXTO de
# tesouraria com hedge cambial — muito melhor analog para "pagamento cross-border" do que
# o Nubank (banco, balanço de depósitos/carteira), que era a âncora anterior.
#
# ⚠️ Honestidade de dados: cada campo é rotulado (REAL, com fonte) ou (ILUSTRATIVO, premissa).
# Ressalva adicional: a Azul passou por reestruturação de dívida em jan/2025 (US$1,6bi extintos,
# oferta de US$525mi em Superpriority Notes) — o que REFORÇA, não enfraquece, o ponto: gestão
# de exposição em USD é existencial para esse perfil de empresa.

# --- (REAL) Azul S.A. FY2024, Form 20-F protocolado na SEC (fev/2025) ---
AZUL_FY2024 = {
    "receita_total_brl_bi": 19.5,            # receita operacional recorde 2024
    "liquidez_imediata_brl_bi": 3.1,         # caixa + equivalentes + recebíveis + invest. curto prazo
    "liquidez_total_brl_bi": 7.5,            # inclui depósitos, reservas de manutenção, longo prazo
    "ptax_divida_usd": 6.19,                 # câmbio de fim de trimestre usado no cronograma da dívida USD
    "fonte": "https://www.sec.gov/Archives/edgar/data/1432364/000162828025020401/azul-20241231.htm",
    "nota": "Reestruturação de dívida em jan/2025 (US$1,6bi extintos) — exposição USD é existencial.",
}

# --- (ILUSTRATIVO) tesouraria operacional sintética nessa escala e perfil de exposição ---
# Base = liquidez TOTAL (~R$7,5bi: caixa + depósitos + reservas + invest.), que é o que a
# tesouraria de fato gere (não só a imediata). Forte saída em USD (leasing/combustível/
# manutenção), característica da aérea. Números plausíveis, não extraídos linha a linha.
PERFIL_DEMO = {
    "saldo_brl": 4_000_000_000,               # R$ 4,0 bi — caixa operacional (ILUSTRATIVO)
    "saldo_usd": 300_000_000,                 # posição em dólar p/ obrigações USD (ILUSTRATIVO)
    "saldo_usdt": 30_000_000,                 # working capital já no trilho (ILUSTRATIVO)
    "previsao_gasto_brl_30d": 1_500_000_000,  # opex mensal (~R$18bi/ano, margem fina de aérea) (ILUSTRATIVO)
    "previsao_recebimento_usd_30d": 50_000_000,   # receita de rotas internacionais em USD (ILUSTRATIVO)
    "previsao_pagamento_usd_30d": 250_000_000,    # pagamento cross-border: leasing+combustível+manutenção (ILUSTRATIVO)
}