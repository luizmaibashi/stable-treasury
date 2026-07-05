import logging
import time

import numpy as np
import requests

logger = logging.getLogger(__name__)

DEFILLAMA_CHART_URL = "https://coins.llama.fi/chart/coingecko:{id}"


def historico_preco_peg(coingecko_id: str, inicio_unix: int, dias: int = 730) -> list[float]:
    url = DEFILLAMA_CHART_URL.format(id=coingecko_id)
    params = {"start": inicio_unix, "span": dias, "period": "1d"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        chave = f"coingecko:{coingecko_id}"
        pontos = data["coins"][chave]["prices"]
        return [p["price"] for p in pontos]
    except Exception as e:
        logger.warning(f"Falha ao consultar histórico de peg via DefiLlama: {e}")
        return []


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


def var_es_historico(retornos: np.ndarray, confianca: float = 0.99) -> tuple[float, float]:
    perdas = -retornos
    perdas_ordenadas = np.sort(perdas)[::-1]
    n = len(perdas_ordenadas)
    # round() em vez de int() puro: (1-0.9)*10 dá 0.999...998 em ponto flutuante,
    # int() trunca pra 0 e perde 1 caso da cauda inteiro. max(1, ...) garante
    # que sempre existe pelo menos 1 caso na cauda quando confianca < 1.
    tail_count = max(1, round((1 - confianca) * n))
    var = float(perdas_ordenadas[tail_count - 1])
    es = float(perdas_ordenadas[:tail_count].mean())
    return var, es


def avaliar_risco_atual(
    coingecko_id: str, dias: int = 90, confianca: float = 0.97
) -> tuple[str, float, float]:
    # dias=90 (1 trimestre, casa com cadência de attestation e regime atual) e
    # confianca=0.97 (alinhado a Basel FRTB, ES 97,5%) — justificativa no ADR-0004
    inicio = int(time.time()) - dias * 86400
    precos = historico_preco_peg(coingecko_id, inicio, dias=dias)
    if len(precos) < 2:
        # sem dado (API fora do ar): fallback conservador = faixa "medio"
        return "medio", 0.30, 0.0
    desvios = desvio_peg(precos)
    _, es = var_es_historico(desvios, confianca=confianca)
    faixa, teto = classificar_risco_e_teto(es)
    return faixa, teto, es