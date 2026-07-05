from datetime import datetime, timezone

from sqlalchemy import select

from .db import peg_prices, risk_snapshots


def _utc_naive(dt: datetime) -> datetime:
    # SQLite não guarda timezone e Postgres guarda — pra o código se comportar
    # idêntico nos dois, normalizamos tudo pra UTC "naive" na escrita/comparação.
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _com_utc(dt: datetime) -> datetime:
    # na leitura, reanexa UTC: SQLite devolve naive, Postgres devolve aware —
    # coerção garante que o downstream sempre recebe datetime UTC-aware.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def salvar_precos(engine, coingecko_id: str, pontos: list[tuple[datetime, float]]) -> int:
    # idempotência agnóstica de dialeto (SQLite/Postgres): lê os ts já existentes
    # e insere só os novos. Evita ON CONFLICT dialeto-específico. Retorna nº inseridos.
    with engine.begin() as conn:  # begin() = transação com commit automático no fim
        existentes = conn.execute(
            select(peg_prices.c.ts).where(peg_prices.c.coingecko_id == coingecko_id)
        ).scalars().all()
        ja_tem = {_utc_naive(ts) for ts in existentes}
        novos = [
            {"coingecko_id": coingecko_id, "ts": _utc_naive(ts), "price": price}
            for ts, price in pontos
            if _utc_naive(ts) not in ja_tem
        ]
        if novos:
            conn.execute(peg_prices.insert(), novos)  # insert em lote (executemany)
        return len(novos)


def ler_serie_precos(engine, coingecko_id: str) -> list[tuple[datetime, float]]:
    with engine.connect() as conn:
        linhas = conn.execute(
            select(peg_prices.c.ts, peg_prices.c.price)
            .where(peg_prices.c.coingecko_id == coingecko_id)
            .order_by(peg_prices.c.ts)  # ordem cronológica ascendente
        ).all()
    # Numeric volta como Decimal; converte pra float pro consumo downstream (numpy/plot)
    return [(_com_utc(ts), float(price)) for ts, price in linhas]


def salvar_risk_snapshot(
    engine, coingecko_id: str, ts: datetime,
    es: float, var: float, faixa: str, teto: float,
) -> None:
    ts_norm = _utc_naive(ts)
    linha = {
        "coingecko_id": coingecko_id, "ts": ts_norm,
        "es": es, "var": var, "faixa": faixa, "teto": teto,
    }
    with engine.begin() as conn:
        # apaga snapshot pré-existente do mesmo (ativo, ts) antes de inserir:
        # risco é recalculável, então sobrescrever é o comportamento correto.
        conn.execute(
            risk_snapshots.delete().where(
                (risk_snapshots.c.coingecko_id == coingecko_id)
                & (risk_snapshots.c.ts == ts_norm)
            )
        )
        conn.execute(risk_snapshots.insert(), [linha])


def ler_serie_risco(engine, coingecko_id: str) -> list[dict]:
    with engine.connect() as conn:
        linhas = conn.execute(
            select(risk_snapshots)
            .where(risk_snapshots.c.coingecko_id == coingecko_id)
            .order_by(risk_snapshots.c.ts)
        ).mappings().all()  # mappings() = cada linha vira dict-like
    return [
        {
            "ts": _com_utc(r["ts"]), "es": float(r["es"]), "var": float(r["var"]),
            "faixa": r["faixa"], "teto": float(r["teto"]),
        }
        for r in linhas
    ]