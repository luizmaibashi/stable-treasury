# Liquidity Optimizer — conforme finanças de tesouraria corporativa (ADR-0009).
#
# Estrutura de tiers de empresa grande:
#   - Reserva operacional (CASH ONLY): dimensionada por DCOH (days cash on hand), em BRL.
#     Stablecoin NÃO é caixa equivalente (US GAAP/IFRS, ASU 2023-08) — excluída da reserva.
#   - Stablecoin = capital de giro EM TRÂNSITO no trilho cross-border, não investimento.
#     Dimensionada pelo fluxo de pagamento cross-border × janela de settlement.
#   - Teto triplo sobre stablecoin: min(necessidade de giro, cap de política,
#     teto de depeg [ES, do Depeg Engine], espaço fora da reserva).
#   - ES vira haircut de liquidez da stablecoin.
from .coletor_precos import ptax_venda, PTAX_FALLBACK
from .depeg_risk import ES_STRESSED_FLOOR_SVB

# Parâmetros de política (defaults conservadores, configuráveis — ADR-0009 §2)
DCOH_RESERVA_DIAS = 60            # 2 meses de opex em cash (buffer operacional de empresa grande)
DIAS_SETTLEMENT = 5              # janela de liquidação cross-border/off-ramp (T+2 a T+5)
CAP_POLITICA_STABLECOIN = 0.05   # topo do sleeve de ativos digitais aprovável por board (1–5%)


def otimizar_alocacao(
    saldo_brl: float = 0,
    saldo_usdt: float = 0,
    saldo_usd: float = 0,
    previsao_gasto_brl_30d: float = 0,
    previsao_recebimento_usd_30d: float = 0,
    previsao_pagamento_usd_30d: float = 0,
    faixa_risco_stablecoin: str = "medio",
    teto_stablecoin: float = 0.30,
    es_stablecoin: float = 0.0,
    dcoh_reserva_dias: int = DCOH_RESERVA_DIAS,
    dias_settlement: int = DIAS_SETTLEMENT,
    cap_politica_stablecoin: float = CAP_POLITICA_STABLECOIN,
) -> dict:
    ptax = ptax_venda() or PTAX_FALLBACK
    total_brl = saldo_brl + (saldo_usdt * ptax) + (saldo_usd * ptax)
    exportador = previsao_recebimento_usd_30d > 0
    # Achado #6 (auditoria 2026-07-30): a decisão de hedge precisa olhar a EXPOSIÇÃO
    # LÍQUIDA (recebimento - pagamento), não só "tem recebimento em USD?". Uma empresa
    # com passivo pesado em USD (ex: aérea com leasing/combustível) pode ter recebimento
    # > 0 e ainda assim ser líquida SHORT dólar (recebe 50k, paga 250k) — nesse caso
    # precisa de MAIS hedge em USD, não menos.
    exposicao_liquida_usd_30d = previsao_recebimento_usd_30d - previsao_pagamento_usd_30d
    meses_reserva = saldo_brl / previsao_gasto_brl_30d if previsao_gasto_brl_30d > 0 else 99

    # --- Reserva operacional em CASH (BRL), por DCOH ---
    reserva_necessaria_brl = previsao_gasto_brl_30d * (dcoh_reserva_dias / 30)
    reserva_frac = min(1.0, reserva_necessaria_brl / total_brl) if total_brl > 0 else 0.0

    # --- Stablecoin como working capital em trânsito, com teto triplo ---
    fluxo_pagamento_brl = previsao_pagamento_usd_30d * ptax
    giro_necessario_brl = fluxo_pagamento_brl * (dias_settlement / 30)
    need_frac = giro_necessario_brl / total_brl if total_brl > 0 else 0.0
    stablecoin_frac = max(0.0, min(
        need_frac,                    # só o giro que de fato transita
        cap_politica_stablecoin,      # cap de política (board)
        teto_stablecoin,              # teto de depeg (ES, Depeg Engine)
        1.0 - reserva_frac,           # nunca invade a reserva de cash
    ))

    # --- Resto em cash: reserva em BRL, excedente em USD (exportador) ou BRL ---
    cash_frac = 1.0 - stablecoin_frac
    brl_frac = min(reserva_frac, cash_frac)
    excedente_frac = cash_frac - brl_frac
    if exposicao_liquida_usd_30d != 0:
        # exposição líquida != 0 (long OU short em USD): manter/reforçar hedge natural em
        # USD reduz risco cambial nos dois sentidos. Só quando a exposição é zerada
        # (recebimento == pagamento) o excedente não tem função de hedge e vira BRL.
        usd_frac = excedente_frac
    else:
        usd_frac = 0.0
        brl_frac += excedente_frac

    alocacao_pct = {"BRL": brl_frac, "USD": usd_frac, "stablecoin": stablecoin_frac}

    # --- ES como haircut de liquidez da stablecoin (ADR-0009), com PISO de ES estressado
    # (achados #3/#4): VaR/ES histórico é procíclico — em regime calmo, es_stablecoin medido
    # fica perto de zero e o haircut desapareceria junto, escondendo o risco de cauda que só
    # volta a aparecer quando a próxima crise já começou. O piso (ES real do evento USDC-SVB,
    # mar/2023, medido a 4,18% horário) garante um desconto mínimo de liquidez mesmo em
    # regime calmo. Quando o risco medido é PIOR que o piso (crise real em curso), usa o
    # medido — o piso nunca abranda uma crise real, só evita colapso a zero em calmaria.
    es_haircut = max(es_stablecoin, ES_STRESSED_FLOOR_SVB)
    valor_liquidez_stablecoin_brl = stablecoin_frac * total_brl * (1 - es_haircut)

    # --- Ação de liquidez: gap de reserva em cash ---
    if meses_reserva < (dcoh_reserva_dias / 30):
        recomendacao_liquidez = (
            f"Aumentar reserva BRL para {dcoh_reserva_dias} dias de opex "
            f"(atual: {meses_reserva:.1f} meses)"
        )
        converter_para_brl = max(0.0, reserva_necessaria_brl - saldo_brl)
    else:
        recomendacao_liquidez = f"Reserva BRL confortável ({meses_reserva:.1f} meses)"
        converter_para_brl = 0.0

    if exposicao_liquida_usd_30d > 0:
        recomendacao_cambio = (
            f"Manter posição em USD (recebimento líquido de US$ {exposicao_liquida_usd_30d:,.0f} "
            "em 30d) — hedge natural ativo"
        )
    elif exposicao_liquida_usd_30d < 0:
        recomendacao_cambio = (
            f"Manter/reforçar posição em USD — exposição líquida SHORT de "
            f"US$ {abs(exposicao_liquida_usd_30d):,.0f} em 30d (paga mais dólar do que recebe); "
            "liquidar USD aumentaria o risco cambial, não reduziria"
        )
    else:
        recomendacao_cambio = "Converter USD excedente para BRL ou USDT (exposição cambial líquida zerada)"

    return {
        "saldo_total_equivalent_brl": round(total_brl, 2),
        "meses_reserva_brl": round(meses_reserva, 1),
        "reserva_necessaria_brl": round(reserva_necessaria_brl, 2),
        "brl_target": round(brl_frac * total_brl, 2),
        "manter_usd": round((usd_frac * total_brl) / ptax, 2),
        "converter_usdt_para_brl": round(converter_para_brl, 2),
        "exportador": exportador,
        "exposicao_liquida_usd_30d": exposicao_liquida_usd_30d,
        "recomendacao_cambio": recomendacao_cambio,
        "recomendacao_liquidez": recomendacao_liquidez,
        "alocacao_stablecoin_pct": round(stablecoin_frac, 4),  # realizado (giro capado)
        "faixa_risco_stablecoin": faixa_risco_stablecoin,
        "valor_liquidez_stablecoin_brl": round(valor_liquidez_stablecoin_brl, 2),
        "alocacao_pct": {k: round(v, 4) for k, v in alocacao_pct.items()},
        "sugestao": _gerar_sugestao(total_brl, alocacao_pct, es_haircut),
    }


def _gerar_sugestao(total_brl: float, aloc: dict, es: float) -> str:
    partes = [f"{aloc['BRL']:.0%} BRL (reserva cash + liquidez PIX)"]
    if aloc["USD"] > 0:
        partes.append(f"{aloc['USD']:.0%} USD (hedge natural)")
    if aloc["stablecoin"] > 0:
        partes.append(
            f"{aloc['stablecoin']:.1%} stablecoin (giro cross-border em trânsito, "
            f"haircut de depeg {es:.1%})"
        )
    return (
        f"Alocar {total_brl:,.0f} BRL como: " + ", ".join(partes)
        + " [reserva em cash; stablecoin só como capital de giro no trilho, ADR-0009]"
    )