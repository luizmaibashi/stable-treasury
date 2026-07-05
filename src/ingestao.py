import time

import numpy as np

from .depeg_risk import (
    historico_pontos_peg, desvio_peg, var_es_historico, classificar_risco_e_teto,
)
from .repositorio import salvar_precos, ler_serie_precos, salvar_risk_snapshot

# DefiLlama rejeita span > ~500 dias/chamada; 450 dá margem de segurança.
CHUNK_DIAS_PADRAO = 450
STABLECOINS_PADRAO = ("usd-coin", "tether")
INICIO_2022_UNIX = 1_640_995_200  # 2022-01-01 00:00 UTC


def janelas_paginacao(
    inicio_unix: int, fim_unix: int, chunk_dias: int = CHUNK_DIAS_PADRAO
) -> list[tuple[int, int]]:
    # quebra o período [inicio, fim] em janelas de no máx. chunk_dias.
    # retorna lista de (start_unix, dias) — lógica pura, sem rede (testável).
    janelas = []
    cursor = inicio_unix
    passo = chunk_dias * 86400
    while cursor < fim_unix:
        dias_restantes = (fim_unix - cursor) // 86400
        dias = min(chunk_dias, dias_restantes) or 1  # nunca 0
        janelas.append((cursor, dias))
        cursor += passo
    return janelas


def ingerir_historico(
    engine, coingecko_id: str, inicio_unix: int, fim_unix: int,
    chunk_dias: int = CHUNK_DIAS_PADRAO,
) -> int:
    # baixa cada janela da DefiLlama e persiste; salvar_precos é idempotente,
    # então sobreposição entre janelas não duplica. Retorna total inserido.
    total = 0
    for start, dias in janelas_paginacao(inicio_unix, fim_unix, chunk_dias):
        pontos = historico_pontos_peg(coingecko_id, start, dias=dias)
        total += salvar_precos(engine, coingecko_id, pontos)
        time.sleep(0.3)  # gentileza com a API pública (evita rate limit)
    return total


def backfill_completo(
    engine, coins: tuple[str, ...] = STABLECOINS_PADRAO, inicio_unix: int = INICIO_2022_UNIX
) -> dict[str, int]:
    fim_unix = int(time.time())
    return {
        coin: ingerir_historico(engine, coin, inicio_unix, fim_unix)
        for coin in coins
    }


def gerar_snapshots_risco_historico(
    engine, coingecko_id: str, janela_dias: int = 90, passo_dias: int = 7,
    confianca: float = 0.97,
) -> int:
    # backtest: percorre a série de preços já persistida com janela deslizante,
    # calcula VaR/ES em cada ponto e salva o snapshot. É o que alimenta o gráfico
    # histórico de risco e mostra o que o modelo "teria feito" em cada momento.
    serie = ler_serie_precos(engine, coingecko_id)  # [(ts, price)] ordenado
    if len(serie) < janela_dias:
        return 0

    precos = [p for _, p in serie]
    n = len(serie)
    # janelas de passo em passo; garante o ponto final (risco mais recente) sempre incluído
    fins = list(range(janela_dias, n + 1, passo_dias))
    if fins[-1] != n:
        fins.append(n)

    gerados = 0
    for fim in fins:
        ini = fim - janela_dias
        desvios = desvio_peg(precos[ini:fim])
        var, es = var_es_historico(np.asarray(desvios), confianca=confianca)
        faixa, teto = classificar_risco_e_teto(es)
        ts_snapshot = serie[fim - 1][0]  # data do último ponto da janela
        salvar_risk_snapshot(
            engine, coingecko_id, ts_snapshot, es=es, var=var, faixa=faixa, teto=teto
        )
        gerados += 1
    return gerados