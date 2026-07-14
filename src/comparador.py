import polars as pl
from .iof_tabela import aliquota_iof
from .coletor_precos import (
    preco_stablecoin, preco_eth, preco_matic, gas_fee_eth, gas_fee_polygon,
    ptax_venda, PTAX_FALLBACK,
)
from .compliance import filtrar_trilhos_permitidos

SPREAD_WIRE_PERCENT = 2.5
TARIFA_WIRE_FIXA_USD = 25.0
GAS_UNITS_ERC20 = 65000
GAS_UNITS_POLYGON = 65000  # mesmo contrato USDT, gas similar ao mainnet

# Custo de conversão do trilho stablecoin (ADR-0008). O trilho não é gratuito:
# BRL→USDT (on-ramp, prêmio real de mercado) + gas + USDT→USD (off-ramp, fixo).
SPREAD_OFFRAMP_PERCENT = 0.3  # venda stablecoin→USD em mercado profundo (constante conservadora)
SPREAD_ONRAMP_FALLBACK_PERCENT = {"usdt": 0.5, "usdc": 0.3}  # usado só se o preço ao vivo falhar

# Trilhos elegíveis por caso de uso (F2, ADR-0008): PIX é doméstico e não disputa
# pagamento cross-border; Wire/USDT/USDC convertem BRL↔USD e não fazem sentido doméstico.
_TRILHOS_DOMESTICO = ("PIX",)
_TRILHOS_CROSS_BORDER = ("Wire (SWIFT)", "USDT (ERC-20)", "USDT (Polygon)", "USDC (ERC-20)", "USDC (Polygon)")


def premio_onramp(preco_stable_brl: float | None, ptax: float, moeda: str) -> float:
    # prêmio de comprar a stablecoin com BRL, como fração (ex: 0,005 = 0,5%).
    # dado real quando disponível; fallback fixo se a cotação ao vivo falhar (ADR-0008).
    if preco_stable_brl is None or ptax <= 0:
        return SPREAD_ONRAMP_FALLBACK_PERCENT[moeda] / 100
    return max(0.0, preco_stable_brl / ptax - 1)


def comparar_custos(
    valor_brl: float,
    tipo_operacao: str = "remessa_internacional_terceiros",
    caso_uso: str = "cross_border",
    eletronico_cambio: bool = False,
) -> pl.DataFrame:
    iof = aliquota_iof(tipo_operacao)
    ptax = ptax_venda() or PTAX_FALLBACK
    valor_usd = valor_brl / ptax

    # prêmios de on-ramp derivados do preço real de mercado (ADR-0008)
    premio_usdt = premio_onramp(preco_stablecoin("usdt"), ptax, "usdt")
    premio_usdc = premio_onramp(preco_stablecoin("usdc"), ptax, "usdc")

    gas_eth = gas_fee_eth()
    gas_poly = gas_fee_polygon()
    eth_usd = preco_eth() or 1800.0
    matic_usd = preco_matic() or 0.50
    gas_eth_usd = gas_eth["avg_gwei"] * 1e-9 * GAS_UNITS_ERC20 * eth_usd
    gas_poly_usd = gas_poly["avg_gwei"] * 1e-9 * GAS_UNITS_POLYGON * matic_usd

    construtores = {
        "PIX": lambda: _calcular_brl_pix(),
        "Wire (SWIFT)": lambda: _calcular_brl_wire(valor_usd, iof, ptax),
        "USDT (ERC-20)": lambda: _calcular_stablecoin("USDT (ERC-20)", "USDT → BRL", valor_brl, premio_usdt, gas_eth_usd, ptax),
        "USDT (Polygon)": lambda: _calcular_stablecoin("USDT (Polygon)", "USDT → BRL", valor_brl, premio_usdt, gas_poly_usd, ptax),
        "USDC (ERC-20)": lambda: _calcular_stablecoin("USDC (ERC-20)", "USDC → BRL", valor_brl, premio_usdc, gas_eth_usd, ptax),
        "USDC (Polygon)": lambda: _calcular_stablecoin("USDC (Polygon)", "USDC → BRL", valor_brl, premio_usdc, gas_poly_usd, ptax),
    }

    elegiveis = _TRILHOS_DOMESTICO if caso_uso == "domestico" else _TRILHOS_CROSS_BORDER
    if eletronico_cambio:
        # BCB 561: ativo virtual proibido como trilho de liquidação em eFX (filtro religado, F7)
        rotulos = {"USDT (ERC-20)": "USDT", "USDT (Polygon)": "USDT",
                   "USDC (ERC-20)": "USDC", "USDC (Polygon)": "USDC"}
        elegiveis = tuple(
            t for t in elegiveis
            if filtrar_trilhos_permitidos([rotulos.get(t, t)], "eletronico_cambio")
        )

    resultados = [construtores[t]() for t in elegiveis]
    df = pl.DataFrame(resultados)
    return df.with_columns(
        (pl.col("custo_total_brl") / valor_brl * 100).alias("custo_percent")
    ).sort("custo_total_brl")


def _calcular_brl_wire(valor_usd: float, iof: float, ptax: float) -> dict:
    spread = valor_usd * (SPREAD_WIRE_PERCENT / 100) * ptax
    iof_val = valor_usd * (iof / 100) * ptax
    tarifa = TARIFA_WIRE_FIXA_USD * ptax
    total = spread + iof_val + tarifa
    return {
        "trilho": "Wire (SWIFT)",
        "moeda": "USD → BRL",
        "spread_brl": round(spread, 2),
        "tarifa_brl": round(tarifa, 2),
        "iof_brl": round(iof_val, 2),
        "gas_brl": 0.0,
        "custo_total_brl": round(total, 2),
    }


def _calcular_brl_pix() -> dict:
    return {
        "trilho": "PIX",
        "moeda": "BRL",
        "spread_brl": 0.0,
        "tarifa_brl": 0.0,
        "iof_brl": 0.0,
        "gas_brl": 0.0,
        "custo_total_brl": 0.0,
    }


def _calcular_stablecoin(
    trilho: str, moeda: str, valor_brl: float, premio_onramp_frac: float,
    gas_usd: float, ptax: float,
) -> dict:
    # custo real do trilho stablecoin (ADR-0008, F1): conversão de entrada + gas + saída.
    spread_onramp = valor_brl * premio_onramp_frac
    spread_offramp = valor_brl * (SPREAD_OFFRAMP_PERCENT / 100)
    spread_conversao = spread_onramp + spread_offramp
    gas_brl = gas_usd * ptax
    total = spread_conversao + gas_brl
    return {
        "trilho": trilho,
        "moeda": moeda,
        "spread_brl": round(spread_conversao, 2),  # on-ramp + off-ramp
        "tarifa_brl": 0.0,
        "iof_brl": 0.0,  # stablecoin dribla o IOF de eFX — a arbitragem que a BCB 561 fecha
        "gas_brl": round(gas_brl, 2),
        "custo_total_brl": round(total, 2),
    }


def gerar_faturas_sinteticas() -> pl.DataFrame:
    # perfis rodam em cross_border, onde a escolha de trilho de fato importa (F2)
    perfis = []
    valores = [5000, 50000, 250000, 1000000]
    labels = ["Pequeno (~R$5k)", "Médio (~R$50k)", "Grande (~R$250k)", "Corporativo (~R$1M)"]
    for v, l in zip(valores, labels, strict=False):
        custos = comparar_custos(v, caso_uso="cross_border")
        melhor = custos[0]
        pior = custos[-1]
        perfis.append({
            "perfil": l,
            "valor_brl": v,
            "melhor_trilho": melhor["trilho"][0],
            "custo_melhor_brl": melhor["custo_total_brl"][0],
            "custo_melhor_pct": round(float(melhor["custo_percent"][0]), 2),
            "pior_trilho": pior["trilho"][0],
            "custo_pior_brl": pior["custo_total_brl"][0],
            "custo_pior_pct": round(float(pior["custo_percent"][0]), 2),
        })
    return pl.DataFrame(perfis)