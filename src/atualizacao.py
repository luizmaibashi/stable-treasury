"""Atualiza o histórico persistido apenas quando a demo é acessada defasada."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Mapping

from sqlalchemy import text

from .ingestao import STABLECOINS_PADRAO, gerar_snapshots_risco_historico, ingerir_historico
from .repositorio import ultima_data_preco

TTL_PADRAO = timedelta(hours=24)
SOBREPOSICAO_PADRAO = timedelta(days=1)
_LOCK_ATUALIZACAO = 4_175_202_608


@dataclass(frozen=True)
class ResultadoAtualizacao:
    atualizados: tuple[str, ...] = ()
    falhas: dict[str, str] = field(default_factory=dict)


def atualizar_se_defasado(
    ultimos_pontos: Mapping[str, datetime | None],
    agora: datetime,
    ingerir: Callable[[str, datetime, datetime], object],
    recalcular: Callable[[str], object],
    ttl: timedelta = TTL_PADRAO,
    sobreposicao: timedelta = SOBREPOSICAO_PADRAO,
) -> ResultadoAtualizacao:
    """Busca somente o delta vencido; uma falha mantém o último estado íntegro."""
    _validar_datetime_utc(agora, "agora")
    atualizados: list[str] = []
    falhas: dict[str, str] = {}

    for ativo, ultimo_ponto in ultimos_pontos.items():
        if ultimo_ponto is None:
            raise ValueError(f"Histórico ausente para {ativo}; execute o seed explicitamente.")
        _validar_datetime_utc(ultimo_ponto, f"último ponto de {ativo}")
        if agora - ultimo_ponto <= ttl:
            continue

        try:
            inseridos = ingerir(ativo, ultimo_ponto - sobreposicao, agora)
            if inseridos == 0:
                falhas[ativo] = "A fonte não retornou novos preços."
                continue
            recalcular(ativo)
            atualizados.append(ativo)
        except Exception as erro:  # fonte externa não pode derrubar a demonstração
            falhas[ativo] = str(erro)

    return ResultadoAtualizacao(tuple(atualizados), falhas)


def atualizar_historico_do_banco(engine) -> ResultadoAtualizacao:
    """Orquestra a atualização no banco sem executar backfill implícito."""
    with lock_atualizacao(engine) as adquiriu_lock:
        if not adquiriu_lock:
            return ResultadoAtualizacao()

        agora = datetime.now(timezone.utc)
        ultimos_pontos = {ativo: ultima_data_preco(engine, ativo) for ativo in STABLECOINS_PADRAO}

        def ingerir_delta(ativo: str, inicio: datetime, fim: datetime) -> int:
            return ingerir_historico(engine, ativo, int(inicio.timestamp()), int(fim.timestamp()))

        def recalcular_risco(ativo: str) -> int:
            return gerar_snapshots_risco_historico(engine, ativo)

        return atualizar_se_defasado(
            ultimos_pontos, agora, ingerir=ingerir_delta, recalcular=recalcular_risco
        )


@contextmanager
def lock_atualizacao(engine):
    """Evita refresh duplicado entre sessões Streamlit no Postgres de produção."""
    if engine.dialect.name != "postgresql":
        yield True
        return

    with engine.connect() as conn:
        adquiriu_lock = bool(
            conn.execute(text("SELECT pg_try_advisory_lock(:chave)"), {"chave": _LOCK_ATUALIZACAO}).scalar()
        )
        try:
            yield adquiriu_lock
        finally:
            if adquiriu_lock:
                conn.execute(text("SELECT pg_advisory_unlock(:chave)"), {"chave": _LOCK_ATUALIZACAO})


def _validar_datetime_utc(valor: datetime, nome: str) -> None:
    if valor.tzinfo is None or valor.utcoffset() is None:
        raise ValueError(f"{nome} precisa ter timezone UTC explícito.")
