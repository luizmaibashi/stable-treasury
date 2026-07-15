import logging
import time
from datetime import datetime, timezone

import numpy as np
import requests

logger = logging.getLogger(__name__)

DEFILLAMA_CHART_URL = "https://coins.llama.fi/chart/coingecko:{id}"
MAX_PONTOS_POR_CHAMADA = 500  # limite duro da DefiLlama por requisição


def _fetch_chart(coingecko_id: str, inicio_unix: int, span: int, period: str) -> list[tuple[datetime, float]]:
    # chamada única à DefiLlama (span = nº de períodos, ≤ 500). Base de tudo.
    url = DEFILLAMA_CHART_URL.format(id=coingecko_id)
    params = {"start": inicio_unix, "span": span, "period": period}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        pontos = resp.json()["coins"][f"coingecko:{coingecko_id}"]["prices"]
        return [
            (datetime.fromtimestamp(p["timestamp"], tz=timezone.utc), float(p["price"]))
            for p in pontos
        ]
    except Exception as e:
        logger.warning(f"Falha ao consultar histórico de peg via DefiLlama: {e}")
        return []


def historico_pontos_peg(
    coingecko_id: str, inicio_unix: int, dias: int = 730
) -> list[tuple[datetime, float]]:
    # versão diária com timestamp: retorna (datetime UTC, preço) — base pra persistência/backtest.
    return _fetch_chart(coingecko_id, inicio_unix, dias, "1d")


def janelas_horarias(
    inicio_unix: int, fim_unix: int, max_pontos: int = MAX_PONTOS_POR_CHAMADA
) -> list[tuple[int, int]]:
    # quebra [inicio, fim] em janelas de ≤ max_pontos HORAS (limite da API). Lógica pura,
    # sem rede (testável). Retorna [(start_unix, span_horas)].
    janelas = []
    cursor = inicio_unix
    passo = max_pontos * 3600
    while cursor < fim_unix:
        horas_restantes = (fim_unix - cursor) // 3600
        span = min(max_pontos, horas_restantes) or 1
        janelas.append((cursor, span))
        cursor += passo
    return janelas


def historico_pontos_peg_horario(
    coingecko_id: str, dias: int = 90
) -> list[tuple[datetime, float]]:
    # série HORÁRIA paginada (respeita o teto de 500 pontos/chamada). Usada pro risco
    # ATUAL, onde a robustez de cauda importa: 90 dias horário = ~2160 pontos (cauda de
    # ~65 a 97%) vs. 90 diário (cauda de 3). Deduplicado e ordenado por timestamp.
    fim = int(time.time())
    inicio = fim - dias * 86400
    vistos: dict[datetime, float] = {}
    for start, span in janelas_horarias(inicio, fim):
        for ts, price in _fetch_chart(coingecko_id, start, span, "1h"):
            vistos[ts] = price
        time.sleep(0.3)  # cortesia com a API pública
    return sorted(vistos.items())


def historico_preco_peg(coingecko_id: str, inicio_unix: int, dias: int = 730) -> list[float]:
    # atalho pros consumidores que só querem a série de preços (ex: avaliar_risco_atual)
    return [price for _, price in historico_pontos_peg(coingecko_id, inicio_unix, dias)]


def desvio_peg(precos: list[float]) -> np.ndarray:
    # métrica de risco correta pra stablecoin: distância direta do peg (preço - 1,00),
    # não retorno dia-a-dia — uma queda gradual de $1,00 a $0,90 em vários passos pequenos
    # tem retorno diário baixo, mas o desvio acumulado revela o depeg real.
    return np.array(precos) - 1.0


# faixas calibradas com ES real dos 2 eventos históricos — justificativa completa
# (cortes, tetos, confiança 97%, janela 90d) documentada no ADR-0004:
# USDC-SVB (recuperável) = 1,76% ES -> "baixo"; UST (catastrófico) = 99,32% ES -> "alto".
# "medio" é buffer conservador pra cenário grave não observado em stablecoin fiat-backed.
FAIXAS_RISCO = [
    ("baixo", 0.05, 0.60),
    ("medio", 0.30, 0.30),
    ("alto", float("inf"), 0.10),
]


def classificar_risco_e_teto(es: float) -> tuple[str, float]:
    for nome, limite_superior, teto in FAIXAS_RISCO:
        if es < limite_superior:
            return nome, teto
    return FAIXAS_RISCO[-1][0], FAIXAS_RISCO[-1][2]


def tamanho_cauda(n_amostras: int, confianca: float = 0.97) -> int:
    # nº de observações na cauda que formam o ES. Exposto pra transparência de robustez:
    # janela curta + confiança alta => cauda rasa (ex: 90 dias @ 97% => 3 amostras),
    # ES ruidoso e sensível a outlier (achado F4 da auditoria 2026-07-14).
    return max(1, round((1 - confianca) * n_amostras))


def var_es_historico(retornos: np.ndarray, confianca: float = 0.99) -> tuple[float, float]:
    if len(retornos) == 0:
        # falha alta e clara: retornar (0.0, 0.0) mentiria "risco zero" quando
        # na verdade é "sem dado pra concluir nada" (achado do PAVC audit).
        raise ValueError("var_es_historico recebeu array de retornos vazio — sem dado pra calcular risco")
    perdas = -retornos
    perdas_ordenadas = np.sort(perdas)[::-1]
    n = len(perdas_ordenadas)
    # round() em vez de int() puro: (1-0.9)*10 dá 0.999...998 em ponto flutuante,
    # int() trunca pra 0 e perde 1 caso da cauda inteiro. max(1, ...) garante
    # que sempre existe pelo menos 1 caso na cauda quando confianca < 1.
    tail_count = tamanho_cauda(n, confianca)
    var = float(perdas_ordenadas[tail_count - 1])
    es = float(perdas_ordenadas[:tail_count].mean())
    return var, es


def desvio_carteira(series_por_id: dict[str, list], pesos: dict[str, float]) -> np.ndarray:
    # desvio de peg PONDERADO da carteira (ADR-0011, corrige débito #7). Alinha as séries
    # por timestamp comum (inner join) e soma os desvios ponderados pelos pesos normalizados.
    # A correlação entre USDT e USDC EMERGE do dado — não é imposta por fórmula. Medir o risco
    # sobre a carteira real é mais correto que medir só sobre USDC e aplicar ao total.
    total = sum(pesos.values())
    if total <= 0:
        return np.array([])
    w = {i: pesos[i] / total for i in pesos}
    mapas = {i: dict(s) for i, s in series_por_id.items() if i in pesos}
    if not mapas:
        return np.array([])
    ts_comuns = set.intersection(*[set(m.keys()) for m in mapas.values()])
    desvios = [
        sum(w[i] * (mapas[i][ts] - 1.0) for i in mapas)
        for ts in sorted(ts_comuns)
    ]
    return np.array(desvios)


def avaliar_risco_carteira(
    pesos: dict[str, float], dias: int = 90, confianca: float = 0.97
) -> tuple[str, float, float]:
    # risco de depeg da CARTEIRA real (ex: {"usd-coin": 0.6, "tether": 0.4}), série horária.
    # Substitui "medir só USDC e aplicar ao total" pela medição ponderada (débito #7, ADR-0011).
    series = {i: historico_pontos_peg_horario(i, dias=dias) for i in pesos}
    desvios = desvio_carteira(series, pesos)
    if len(desvios) < 2:
        return "medio", 0.30, 0.0  # dado insuficiente → fallback conservador
    _, es = var_es_historico(desvios, confianca=confianca)
    faixa, teto = classificar_risco_e_teto(es)
    return faixa, teto, es


def avaliar_risco_atual(
    coingecko_id: str, dias: int = 90, confianca: float = 0.97, granularidade: str = "1h"
) -> tuple[str, float, float]:
    # dias=90 (1 trimestre, casa com cadência de attestation e regime atual) e
    # confianca=0.97 (alinhado a Basel FRTB, ES 97,5%) — justificativa no ADR-0004.
    # granularidade="1h" (ADR-0011): 90 dias horário = ~2160 pontos → cauda de ~65 a 97%
    # (robusta) e captura o mínimo intra-dia real (USDC tocou 0,8767 em mar/2023), que a
    # série diária suavizava pra ~0,96. Cai pra diário se o horário vier insuficiente.
    if granularidade == "1h":
        precos = [p for _, p in historico_pontos_peg_horario(coingecko_id, dias=dias)]
        if len(precos) < 2:  # horário indisponível → tenta diário antes de desistir
            inicio = int(time.time()) - dias * 86400
            precos = historico_preco_peg(coingecko_id, inicio, dias=dias)
    else:
        inicio = int(time.time()) - dias * 86400
        precos = historico_preco_peg(coingecko_id, inicio, dias=dias)

    if len(precos) < 2:
        # sem dado (API fora do ar): fallback conservador = faixa "medio"
        return "medio", 0.30, 0.0
    desvios = desvio_peg(precos)
    _, es = var_es_historico(desvios, confianca=confianca)
    faixa, teto = classificar_risco_e_teto(es)
    return faixa, teto, es