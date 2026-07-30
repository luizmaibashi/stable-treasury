import polars as pl
from .iof_tabela import aliquota_iof
from .coletor_precos import (
    preco_stablecoin, preco_eth, preco_matic, gas_fee_eth, gas_fee_polygon,
    ptax_venda, PTAX_FALLBACK, order_book_usdt_brl, order_book_usdc_brl,
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

# Slippage por volume (ADR-0007 ponto C / ADR-0010): converter volume grande move o mercado.
# ⚠️ APROXIMAÇÃO DOCUMENTADA — acréscimo por faixa, NÃO modelo de order book real (débito #11).
# Faixas: (limite superior em BRL, acréscimo em % sobre o valor convertido)
FAIXAS_SLIPPAGE = [
    (100_000, 0.0),
    (1_000_000, 0.1),
    (10_000_000, 0.25),
    (float("inf"), 0.5),
]


def slippage_por_volume(valor_brl: float) -> float:
    # FALLBACK heurístico (usado se o order book real não estiver disponível).
    # retorna o acréscimo de slippage como fração (ex: 0,0025 = 0,25%)
    for limite, pct in FAIXAS_SLIPPAGE:
        if valor_brl < limite:
            return pct / 100
    return FAIXAS_SLIPPAGE[-1][1] / 100


def vwap_execucao(niveis: list[list[float]], valor_brl: float) -> float | None:
    # preço médio de execução (VWAP) ao comprar `valor_brl` caminhando o order book
    # nível a nível [[preco, qty], ...]. Retorna None se o book for raso demais pro volume.
    # Isto é microestrutura de mercado real, não estimativa por faixa (ADR-0011).
    gasto = 0.0
    qty_total = 0.0
    for preco, qty in niveis:
        custo_nivel = preco * qty
        if gasto + custo_nivel >= valor_brl:
            falta = valor_brl - gasto
            qty_total += falta / preco
            return valor_brl / qty_total  # preço médio de execução
        gasto += custo_nivel
        qty_total += qty
    return None  # profundidade insuficiente


def _mid_do_book(book: dict | None) -> float | None:
    if book and book["asks"] and book["bids"]:
        return (book["asks"][0][0] + book["bids"][0][0]) / 2
    return None


def _slippage_do_book(book: dict | None, valor_brl: float) -> float:
    mid = _mid_do_book(book)
    if mid is not None and mid > 0:
        vwap = vwap_execucao(book["asks"], valor_brl)
        if vwap is not None:
            return max(0.0, (vwap - mid) / mid)
    return slippage_por_volume(valor_brl)  # fallback documentado


def slippage_execucao(valor_brl: float, moeda: str = "usdt") -> float:
    # slippage MEDIDO no order book real (Binance) DA MOEDA CERTA: (VWAP − mid) / mid.
    # Achado #9 (auditoria 2026-07-30): USDC/BRL tem profundidade própria e menor que
    # USDT/BRL no Brasil — usar sempre o book do USDT subestimava o slippage do USDC.
    # Cai pro fallback heurístico (slippage_por_volume) se a API falhar ou o book não
    # cobrir o volume. Despacho direto (não via dict de módulo) pra resolver a função
    # em tempo de chamada — permite monkeypatch de `order_book_usdt_brl`/`_usdc_brl`.
    book = order_book_usdt_brl() if moeda == "usdt" else order_book_usdc_brl()
    return _slippage_do_book(book, valor_brl)


# Achado #8 (auditoria 2026-07-30): acima deste limiar, a divergência entre a PTAX
# (BCB, D-1) e o mid do order book (Binance, tempo real) provavelmente domina o número
# do prêmio de on-ramp — não é possível "corrigir" sem FX intradiário oficial gratuito
# (não existe); a correção honesta é EXPOR a defasagem, não escondê-la (ADR-0011 §6).
LIMIAR_DEFASAGEM_PTAX_PERCENT = 1.0


def _defasagem_pct(mid: float | None, ptax: float) -> float | None:
    if mid is None or ptax <= 0:
        return None
    return (mid - ptax) / ptax * 100

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
    spread_wire_percent: float = SPREAD_WIRE_PERCENT,
) -> pl.DataFrame:
    # Achado #1 (auditoria 2026-07-30): SPREAD_WIRE_PERCENT era constante fixa (2,5%, spread
    # de varejo/PME). Tesouraria corporativa negocia 0,2–0,8% em ticket grande — e a economia
    # do stablecoin depende diretamente desse número, tanto quanto do IOF. Virou parâmetro
    # (default preserva o comportamento anterior) em vez de premissa escondida.
    iof = aliquota_iof(tipo_operacao)
    ptax = ptax_venda() or PTAX_FALLBACK
    valor_usd = valor_brl / ptax

    # prêmios de on-ramp derivados do preço real de mercado (ADR-0008)
    premio_usdt = premio_onramp(preco_stablecoin("usdt"), ptax, "usdt")
    premio_usdc = premio_onramp(preco_stablecoin("usdc"), ptax, "usdc")

    # Achado #9 (auditoria 2026-07-30): book buscado 1x por MOEDA (não por trilho) —
    # ERC-20 e Polygon da mesma stablecoin compartilham o mesmo book on/off-chain de USD↔BRL,
    # então consultar 2x o mesmo book (ERC-20 e Polygon) era rede redundante.
    book_usdt = order_book_usdt_brl()
    book_usdc = order_book_usdc_brl()
    slippage_usdt = _slippage_do_book(book_usdt, valor_brl)
    slippage_usdc = _slippage_do_book(book_usdc, valor_brl)
    # Achado #8: mesmo book já buscado acima — a defasagem PTAX×Binance é subproduto,
    # não uma chamada de rede extra.
    defasagem_usdt = _defasagem_pct(_mid_do_book(book_usdt), ptax)
    defasagem_usdc = _defasagem_pct(_mid_do_book(book_usdc), ptax)

    gas_eth = gas_fee_eth()
    gas_poly = gas_fee_polygon()
    eth_usd = preco_eth() or 1800.0
    matic_usd = preco_matic() or 0.50
    gas_eth_usd = gas_eth["avg_gwei"] * 1e-9 * GAS_UNITS_ERC20 * eth_usd
    gas_poly_usd = gas_poly["avg_gwei"] * 1e-9 * GAS_UNITS_POLYGON * matic_usd

    construtores = {
        "PIX": lambda: _calcular_brl_pix(),
        "Wire (SWIFT)": lambda: _calcular_brl_wire(valor_usd, iof, ptax, spread_wire_percent),
        "USDT (ERC-20)": lambda: _calcular_stablecoin("USDT (ERC-20)", "USDT → BRL", valor_brl, premio_usdt, slippage_usdt, gas_eth_usd, ptax, defasagem_usdt),
        "USDT (Polygon)": lambda: _calcular_stablecoin("USDT (Polygon)", "USDT → BRL", valor_brl, premio_usdt, slippage_usdt, gas_poly_usd, ptax, defasagem_usdt),
        "USDC (ERC-20)": lambda: _calcular_stablecoin("USDC (ERC-20)", "USDC → BRL", valor_brl, premio_usdc, slippage_usdc, gas_eth_usd, ptax, defasagem_usdc),
        "USDC (Polygon)": lambda: _calcular_stablecoin("USDC (Polygon)", "USDC → BRL", valor_brl, premio_usdc, slippage_usdc, gas_poly_usd, ptax, defasagem_usdc),
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


def spread_indiferenca_wire(
    valor_brl: float, tipo_operacao: str = "remessa_internacional_terceiros",
) -> float:
    # Achado #1 (auditoria 2026-07-30): em vez de vender "~90% de economia" como fato fixo,
    # calcula o spread de Wire (%) em que a conclusão INVERTE — abaixo dele, Wire fica mais
    # barato que o melhor trilho stablecoin. Isola o custo de Wire em spread=0 (só
    # iof + tarifa fixa) e resolve algebricamente: custo_wire(spread%) é linear em spread%,
    # custo do stablecoin não depende de spread_wire_percent.
    # Resultado negativo = stablecoin vence mesmo com spread negociado de 0% (a folga do
    # IOF já cobre tudo); positivo = existe um spread real acima do qual o stablecoin ganha.
    df = comparar_custos(valor_brl, tipo_operacao, caso_uso="cross_border", spread_wire_percent=0.0)
    ptax = ptax_venda() or PTAX_FALLBACK
    valor_usd = valor_brl / ptax
    wire_com_spread_zero = df.filter(pl.col("trilho") == "Wire (SWIFT)")["custo_total_brl"][0]
    melhor_stablecoin = df.filter(pl.col("trilho") != "Wire (SWIFT)")["custo_total_brl"].min()
    return (melhor_stablecoin - wire_com_spread_zero) / (valor_usd * ptax) * 100


def _calcular_brl_wire(
    valor_usd: float, iof: float, ptax: float, spread_wire_percent: float = SPREAD_WIRE_PERCENT,
) -> dict:
    spread = valor_usd * (spread_wire_percent / 100) * ptax
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
        "defasagem_ptax_binance_pct": None,  # não se aplica a trilho não-cripto
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
        "defasagem_ptax_binance_pct": None,
    }


def _calcular_stablecoin(
    trilho: str, moeda: str, valor_brl: float, premio_onramp_frac: float,
    slippage_frac: float, gas_usd: float, ptax: float,
    defasagem_ptax_binance_pct: float | None = None,
) -> dict:
    # custo real do trilho stablecoin (ADR-0008, F1): conversão de entrada + gas + saída.
    # On-ramp = prêmio spot (dado real) + slippage MEDIDO no order book (ADR-0011, VWAP real),
    # pré-calculado 1x por moeda em comparar_custos (achado #9, evita rede redundante e
    # book errado entre ERC-20/Polygon da mesma stablecoin).
    spread_onramp = valor_brl * (premio_onramp_frac + slippage_frac)
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
        # Achado #8: divergência PTAX (D-1) × Binance mid (tempo real), em %. Acima de
        # LIMIAR_DEFASAGEM_PTAX_PERCENT, o prêmio de on-ramp acima provavelmente reflete
        # câmbio se movendo intradia, não custo real de liquidez do trilho — disclaimer,
        # não correção (não existe FX oficial intradiário gratuito).
        "defasagem_ptax_binance_pct": (
            round(defasagem_ptax_binance_pct, 4) if defasagem_ptax_binance_pct is not None else None
        ),
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