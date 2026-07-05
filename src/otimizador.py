# Liquidity Optimizer: alocação de caixa entre BRL / USDT / USD.
# O teto de exposição a stablecoin vem do Depeg Risk Engine (src/depeg_risk.py):
# VaR/ES sobre histórico real de peg, classificado em faixas de risco (ADR-0003).
from .coletor_precos import ptax_venda

# alocação-alvo original em stablecoin, antes de aplicar o teto de risco (Módulo 4b):
# exportador (True) = 50% (USDT flexibilidade), não-exportador (False) = 60% (USDT 40% + USDC 20%)
_ALOCACAO_STABLECOIN_PADRAO = {True: 0.50, False: 0.60}


def otimizar_alocacao(
    saldo_brl: float = 0,
    saldo_usdt: float = 0,
    saldo_usd: float = 0,
    previsao_gasto_brl_30d: float = 0,
    previsao_recebimento_usd_30d: float = 0,
    faixa_risco_stablecoin: str = "medio",
    teto_stablecoin: float = 0.30,
) -> dict:
    ptax = ptax_venda() or 5.7
    total_brl = saldo_brl + (saldo_usdt * ptax) + (saldo_usd * ptax)

    meses_reserva = saldo_brl / previsao_gasto_brl_30d if previsao_gasto_brl_30d > 0 else 99

    if previsao_recebimento_usd_30d > 0:
        exportador = True
        recomendacao_cambio = "Manter posição em USD (receita em dólar) — hedge natural ativo"
        manter_usd = saldo_usd + previsao_recebimento_usd_30d * 0.3
    else:
        exportador = False
        recomendacao_cambio = "Converter USD excedente para BRL ou USDT (sem receita em dólar)"
        manter_usd = saldo_usd * 0.2

    alocacao_stablecoin_pct = min(
        _ALOCACAO_STABLECOIN_PADRAO[exportador], teto_stablecoin
    )

    if meses_reserva < 3:
        recomendacao_liquidez = f"Aumentar reserva BRL para 3 meses de gasto (atual: {meses_reserva:.1f} meses)"
        brl_target = previsao_gasto_brl_30d * 3
        converter_usdt_para_brl = max(0, brl_target - saldo_brl)
    else:
        recomendacao_liquidez = f"Reserva BRL confortável ({meses_reserva:.1f} meses)"
        brl_target = saldo_brl
        converter_usdt_para_brl = 0

    return {
        "saldo_total_equivalent_brl": round(total_brl, 2),
        "meses_reserva_brl": round(meses_reserva, 1),
        "brl_target": round(brl_target, 2),
        "manter_usd": round(manter_usd, 2),
        "converter_usdt_para_brl": round(converter_usdt_para_brl, 2),
        "exportador": exportador,
        "recomendacao_cambio": recomendacao_cambio,
        "recomendacao_liquidez": recomendacao_liquidez,
        "alocacao_stablecoin_pct": alocacao_stablecoin_pct,
        "faixa_risco_stablecoin": faixa_risco_stablecoin,
        "sugestao": _gerar_sugestao(total_brl, exporter=exportador, alocacao_stablecoin_pct=alocacao_stablecoin_pct),
    }


def _gerar_sugestao(total_brl: float, exporter: bool, alocacao_stablecoin_pct: float) -> str:
    # % capado que "sobrou" do corte de risco vira BRL (liquidez PIX) — nunca some
    pct_capado = _ALOCACAO_STABLECOIN_PADRAO[exporter] - alocacao_stablecoin_pct

    if exporter:
        pct_usd = 0.30  # hedge cambial não é afetado pelo teto de risco de stablecoin
        pct_brl = 0.20 + pct_capado
        return (
            f"Alocar {total_brl:,.0f} BRL como: "
            f"{alocacao_stablecoin_pct:.0%} USDT (flexibilidade on-chain, capado por risco de depeg), "
            f"{pct_usd:.0%} USD (hedge natural), "
            f"{pct_brl:.0%} BRL (liquidez PIX)"
        )

    # não-exportador: stablecoin original é 40% USDT + 20% USDC = 60% do total;
    # escala os dois proporcionalmente quando o teto de risco corta o total
    escala = alocacao_stablecoin_pct / _ALOCACAO_STABLECOIN_PADRAO[exporter]
    pct_usdt = 0.40 * escala
    pct_usdc = 0.20 * escala
    pct_brl = 0.40 + pct_capado
    return (
        f"Alocar {total_brl:,.0f} BRL como: "
        f"{pct_brl:.0%} BRL (PIX/liquidez), "
        f"{pct_usdt:.0%} USDT (Polygon, baixo custo), "
        f"{pct_usdc:.0%} USDC (diversificação) "
        f"[teto de stablecoin aplicado por risco de depeg]"
    )
