from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

try:
    from src.atualizacao import atualizar_se_defasado, lock_atualizacao
except ImportError:
    from atualizacao import atualizar_se_defasado, lock_atualizacao


AGORA = datetime(2026, 8, 30, 12, tzinfo=timezone.utc)


class _ResultadoSql:
    def __init__(self, valor):
        self.valor = valor

    def scalar(self):
        return self.valor


class _EnginePostgresFalso:
    def __init__(self, adquiriu_lock):
        self.dialect = SimpleNamespace(name="postgresql")
        self.adquiriu_lock = adquiriu_lock
        self.comandos = []

    @contextmanager
    def connect(self):
        yield self

    def execute(self, comando, _parametros):
        self.comandos.append(str(comando))
        return _ResultadoSql(self.adquiriu_lock)


def test_nao_atualiza_quando_a_serie_ainda_esta_no_ttl():
    chamadas = []

    resultado = atualizar_se_defasado(
        ultimos_pontos={"usd-coin": AGORA - timedelta(hours=23)},
        agora=AGORA,
        ingerir=lambda *_: chamadas.append("ingestao"),
        recalcular=lambda *_: chamadas.append("risco"),
    )

    assert resultado.atualizados == ()
    assert chamadas == []


def test_atualiza_apenas_delta_com_sobreposicao_de_um_dia():
    chamadas = []
    ultimo = AGORA - timedelta(days=30)

    resultado = atualizar_se_defasado(
        ultimos_pontos={"usd-coin": ultimo},
        agora=AGORA,
        ingerir=lambda ativo, inicio, fim: chamadas.append(("ingestao", ativo, inicio, fim)),
        recalcular=lambda ativo: chamadas.append(("risco", ativo)),
    )

    assert resultado.atualizados == ("usd-coin",)
    assert chamadas == [
        ("ingestao", "usd-coin", ultimo - timedelta(days=1), AGORA),
        ("risco", "usd-coin"),
    ]


def test_banco_sem_historico_nao_dispara_backfill_automatico():
    with pytest.raises(ValueError, match="seed"):
        atualizar_se_defasado(
            ultimos_pontos={"usd-coin": None},
            agora=AGORA,
            ingerir=lambda *_: pytest.fail("não deve ingerir"),
            recalcular=lambda *_: pytest.fail("não deve recalcular"),
        )


def test_erro_da_fonte_preserva_resultado_sem_marcar_atualizacao():
    def fonte_indisponivel(*_):
        raise RuntimeError("DefiLlama indisponível")

    resultado = atualizar_se_defasado(
        ultimos_pontos={"usd-coin": AGORA - timedelta(days=2)},
        agora=AGORA,
        ingerir=fonte_indisponivel,
        recalcular=lambda _: pytest.fail("não recalcula após falha"),
    )

    assert resultado.atualizados == ()
    assert resultado.falhas == {"usd-coin": "DefiLlama indisponível"}


def test_rejeita_timestamp_sem_timezone_para_nao_calcular_defasagem_errada():
    with pytest.raises(ValueError, match="timezone UTC explícito"):
        atualizar_se_defasado(
            ultimos_pontos={"usd-coin": datetime(2026, 8, 29, 12)},
            agora=AGORA,
            ingerir=lambda *_: pytest.fail("não deve ingerir"),
            recalcular=lambda *_: pytest.fail("não deve recalcular"),
        )


def test_fonte_sem_novos_pontos_nao_pode_ser_reportada_como_atualizacao():
    resultado = atualizar_se_defasado(
        ultimos_pontos={"usd-coin": AGORA - timedelta(days=2)},
        agora=AGORA,
        ingerir=lambda *_: 0,
        recalcular=lambda _: pytest.fail("não recalcula sem preço novo"),
    )

    assert resultado.atualizados == ()
    assert resultado.falhas == {"usd-coin": "A fonte não retornou novos preços."}


def test_lock_postgres_nega_refresh_simultaneo_sem_tentar_desbloquear_lock_alheio():
    engine = _EnginePostgresFalso(adquiriu_lock=False)

    with lock_atualizacao(engine) as adquiriu_lock:
        assert adquiriu_lock is False

    assert len(engine.comandos) == 1
    assert "pg_try_advisory_lock" in engine.comandos[0]


def test_lock_postgres_libera_apenas_o_lock_que_a_execucao_adquiriu():
    engine = _EnginePostgresFalso(adquiriu_lock=True)

    with lock_atualizacao(engine) as adquiriu_lock:
        assert adquiriu_lock is True

    assert len(engine.comandos) == 2
    assert "pg_advisory_unlock" in engine.comandos[1]
