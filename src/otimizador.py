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
    if exportador:
        usd_frac = excedente_frac      # receita em dólar: excedente vira hedge natural em USD
    else:
        usd_frac = 0.0
        brl_frac += excedente_frac     # sem receita em dólar: excedente fica em BRL

    alocacao_pct = {"BRL": brl_frac, "USD": usd_frac, "stablecoin": stablecoin_frac}

    # --- ES como haircut de liquidez da stablecoin (ADR-0009) ---
    valor_liquidez_stablecoin_brl = stablecoin_frac * total_brl * (1 - es_stablecoin)

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

    recomendacao_cambio = (
        "Manter posição em USD (receita em dólar) — hedge natural ativo" if exportador
        else "Converter USD excedente para BRL ou USDT (sem receita em dólar)"
    )

    return {
        "saldo_total_equivalent_brl": round(total_brl, 2),
        "meses_reserva_brl": round(meses_reserva, 1),
        "reserva_necessaria_brl": round(reserva_necessaria_brl, 2),
        "brl_target": round(brl_frac * total_brl, 2),
        "manter_usd": round((usd_frac * total_brl) / ptax, 2),
        "converter_usdt_para_brl": round(converter_para_brl, 2),
        "exportador": exportador,
        "recomendacao_cambio": recomendacao_cambio,
        "recomendacao_liquidez": recomendacao_liquidez,
        "alocacao_stablecoin_pct": round(stablecoin_frac, 4),  # realizado (giro capado)
        "faixa_risco_stablecoin": faixa_risco_stablecoin,
        "valor_liquidez_stablecoin_brl": round(valor_liquidez_stablecoin_brl, 2),
        "alocacao_pct": {k: round(v, 4) for k, v in alocacao_pct.items()},
        "sugestao": _gerar_sugestao(total_brl, alocacao_pct, es_stablecoin),
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