# Custo de carrego da reserva — 3º pilar (Capital Markets & Funding), ADR-0010.
#
# O capital de uma tesouraria corporativa dorme na RESERVA DE CASH, não no giro em
# stablecoin (que transita em dias). Toda reserva parada tem custo de oportunidade:
# o que ela deixa de render vs. um instrumento de referência que continua sendo
# cash-equivalent (fundo DI / money market / T-bill) — logo, capturável SEM aumentar
# risco e sem violar a regra de reserva cash-only do ADR-0009.
from .coletor_precos import taxa_cdi, taxa_tbill, ptax_venda, PTAX_FALLBACK

DIAS_ANO = 365

# Achado #7 (auditoria 2026-07-30): CDI (BRL) e T-bill (USD) são cash-equivalents em
# MOEDAS diferentes — somar os dois gaps é correto como agregação contábil, mas o
# diferencial CDI−T-bill aproxima, por paridade DESCOBERTA de juros, a depreciação
# esperada do BRL. Ler "gap_total_anual_brl" como dinheiro parado sem risco algum
# esconde que a perna BRL é, em parte, prêmio de carry trade cambial — não é risco
# adicional no sentido do Depeg Engine, mas também não é "sem risco" no sentido de
# custo de carrego de uma reserva de cash. Acima deste limiar, o diferencial já é
# grande o bastante pra dominar a leitura do número. Disclaimer, não correção
# (o diferencial de juros é dado real observável, não um erro a consertar).
LIMIAR_CARRY_TRADE_PERCENT = 5.0


def custo_carrego(
    valor_parado: float, taxa_referencia_pct: float, yield_atual_pct: float = 0.0
) -> dict:
    # gap = o que a referência renderia MENOS o que o caixa já rende hoje.
    # max(0, ...): se o caixa já rende mais que a referência, não há dinheiro na mesa
    # (não faz sentido reportar "custo de oportunidade negativo" como se fosse ganho).
    spread_pct = max(0.0, taxa_referencia_pct - yield_atual_pct)
    gap_anual = valor_parado * (spread_pct / 100)
    return {
        "valor_parado": round(valor_parado, 2),
        "taxa_referencia_pct": taxa_referencia_pct,
        "yield_atual_pct": yield_atual_pct,
        "spread_pct": round(spread_pct, 4),
        "gap_anual": round(gap_anual, 2),
        "gap_diario": round(gap_anual / DIAS_ANO, 2),
    }


def custo_oportunidade_reserva(
    reserva_brl: float,
    posicao_usd: float,
    ptax: float | None = None,
    cdi_pct: float | None = None,
    tbill_pct: float | None = None,
    yield_atual_pct: float = 0.0,
) -> dict:
    # BRL tem CDI como referência; USD tem T-bill. Cada moeda é comparada contra o
    # instrumento cash-equivalent do seu próprio mercado (ADR-0010).
    ptax = ptax if ptax is not None else (ptax_venda() or PTAX_FALLBACK)
    cdi_pct = cdi_pct if cdi_pct is not None else taxa_cdi()
    tbill_pct = tbill_pct if tbill_pct is not None else taxa_tbill()

    brl = custo_carrego(reserva_brl, cdi_pct, yield_atual_pct)
    usd = custo_carrego(posicao_usd, tbill_pct, yield_atual_pct)  # gap em USD
    gap_usd_anual_brl = usd["gap_anual"] * ptax  # converte o gap de USD pra BRL

    total = brl["gap_anual"] + gap_usd_anual_brl
    # Achado #7: diferencial de juros entre as duas moedas de referência — por paridade
    # descoberta de juros, aproxima a depreciação cambial ESPERADA do BRL. Não é erro
    # matemático (a soma dos dois gaps está correta), é contexto que falta na leitura.
    diferencial_juros_cdi_tbill_pct = cdi_pct - tbill_pct
    return {
        "cdi_pct": cdi_pct,
        "tbill_pct": tbill_pct,
        "ptax": ptax,
        "gap_brl_anual": brl["gap_anual"],
        "gap_usd_anual_usd": usd["gap_anual"],
        "gap_usd_anual_brl": round(gap_usd_anual_brl, 2),
        "gap_total_anual_brl": round(total, 2),
        "gap_total_diario_brl": round(total / DIAS_ANO, 2),
        "diferencial_juros_cdi_tbill_pct": round(diferencial_juros_cdi_tbill_pct, 4),
        "alerta_carry_trade": diferencial_juros_cdi_tbill_pct > LIMIAR_CARRY_TRADE_PERCENT,
    }
