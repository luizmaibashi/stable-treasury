import polars as pl
from .iof_tabela import aliquota_iof
from .coletor_precos import preco_stablecoin, preco_eth, preco_matic, gas_fee_eth, gas_fee_polygon, ptax_venda

SPREAD_WIRE_PERCENT = 2.5
TARIFA_WIRE_FIXA_USD = 25.0
GAS_UNITS_ERC20 = 65000
GAS_UNITS_POLYGON = 65000  # mesmo contrato USDT, gas similar ao mainnet


def comparar_custos(valor_brl: float, tipo_operacao: str = "remessa_internacional_terceiros") -> pl.DataFrame:
    iof = aliquota_iof(tipo_operacao)
    ptax = ptax_venda() or 5.0
    usdt_brl = preco_stablecoin("usdt") or ptax * 1.005
    usdc_brl = preco_stablecoin("usdc") or ptax * 1.003
    valor_usd = valor_brl / ptax

    gas_eth = gas_fee_eth()
    gas_poly = gas_fee_polygon()
    eth_usd = preco_eth() or 1800.0
    matic_usd = preco_matic() or 0.50

    gas_eth_usd = gas_eth["avg_gwei"] * 1e-9 * GAS_UNITS_ERC20 * eth_usd
    gas_poly_usd = gas_poly["avg_gwei"] * 1e-9 * GAS_UNITS_POLYGON * matic_usd

    resultados = [
        _calcular_brl_wire(valor_usd, iof, ptax),
        _calcular_brl_pix(valor_brl),
        _calcular_usdt_erc20(gas_eth_usd, ptax),
        _calcular_usdt_polygon(gas_poly_usd, ptax),
        _calcular_usdc_erc20(gas_eth_usd, ptax),
        _calcular_usdc_polygon(gas_poly_usd, ptax),
    ]

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


def _calcular_brl_pix(valor_brl: float) -> dict:
    return {
        "trilho": "PIX",
        "moeda": "BRL",
        "spread_brl": 0.0,
        "tarifa_brl": 0.0,
        "iof_brl": 0.0,
        "gas_brl": 0.0,
        "custo_total_brl": 0.0,
    }


def _calcular_usdt_erc20(gas_usd: float, ptax: float) -> dict:
    gas_brl = gas_usd * ptax
    return {
        "trilho": "USDT (ERC-20)",
        "moeda": "USDT → BRL",
        "spread_brl": 0.0,
        "tarifa_brl": 0.0,
        "iof_brl": 0.0,
        "gas_brl": round(gas_brl, 2),
        "custo_total_brl": round(gas_brl, 2),
    }


def _calcular_usdt_polygon(gas_usd: float, ptax: float) -> dict:
    gas_brl = gas_usd * ptax
    return {
        "trilho": "USDT (Polygon)",
        "moeda": "USDT → BRL",
        "spread_brl": 0.0,
        "tarifa_brl": 0.0,
        "iof_brl": 0.0,
        "gas_brl": round(gas_brl, 2),
        "custo_total_brl": round(gas_brl, 2),
    }


def _calcular_usdc_erc20(gas_usd: float, ptax: float) -> dict:
    gas_brl = gas_usd * ptax
    return {
        "trilho": "USDC (ERC-20)",
        "moeda": "USDC → BRL",
        "spread_brl": 0.0,
        "tarifa_brl": 0.0,
        "iof_brl": 0.0,
        "gas_brl": round(gas_brl, 2),
        "custo_total_brl": round(gas_brl, 2),
    }


def _calcular_usdc_polygon(gas_usd: float, ptax: float) -> dict:
    gas_brl = gas_usd * ptax
    return {
        "trilho": "USDC (Polygon)",
        "moeda": "USDC → BRL",
        "spread_brl": 0.0,
        "tarifa_brl": 0.0,
        "iof_brl": 0.0,
        "gas_brl": round(gas_brl, 2),
        "custo_total_brl": round(gas_brl, 2),
    }


def gerar_faturas_sinteticas() -> pl.DataFrame:
    perfis = []
    valores = [5000, 50000, 250000, 1000000]
    labels = ["Pequeno (~R$5k)", "Médio (~R$50k)", "Grande (~R$250k)", "Corporativo (~R$1M)"]
    for v, l in zip(valores, labels, strict=False):
        custos = comparar_custos(v)
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
