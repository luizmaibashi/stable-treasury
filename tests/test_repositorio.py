from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

try:
    from src.db import init_schema
    from src.repositorio import (
        salvar_precos, ler_serie_precos, salvar_risk_snapshot, ler_serie_risco,
    )
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.db import init_schema
    from src.repositorio import (
        salvar_precos, ler_serie_precos, salvar_risk_snapshot, ler_serie_risco,
    )


def _engine_teste():
    # SQLite em memória com StaticPool: mantém o mesmo banco entre conexões
    # (in-memory normal sumiria a cada nova conexão). Schema vem da metadata única.
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    init_schema(eng)
    return eng


def _dt(dia):
    return datetime(2023, 3, dia, tzinfo=timezone.utc)


def test_salvar_e_ler_precos_em_ordem_cronologica():
    eng = _engine_teste()
    salvar_precos(eng, "usd-coin", [(_dt(12), 0.99), (_dt(11), 0.96)])
    serie = ler_serie_precos(eng, "usd-coin")
    assert len(serie) == 2
    assert serie[0][0] == _dt(11)          # retorna ordenado por ts ascendente
    assert abs(serie[0][1] - 0.96) < 1e-9  # preço do 1º ponto


def test_salvar_precos_idempotente_nao_duplica():
    eng = _engine_teste()
    ponto = [(_dt(11), 0.96)]
    salvar_precos(eng, "usd-coin", ponto)
    salvar_precos(eng, "usd-coin", ponto)  # 2ª ingestão do mesmo ponto
    assert len(ler_serie_precos(eng, "usd-coin")) == 1


def test_salvar_precos_colisao_intra_lote_nao_quebra():
    # PAVC audit: 2 escritas do MESMO ponto colidindo (TOCTOU: SELECT verifica
    # existência, depois INSERT sem atomicidade) lançavam IntegrityError não
    # tratado. Fix: savepoint por linha + except IntegrityError = idempotente.
    #
    # Concorrência real (múltiplas conexões simultâneas) foi verificada à mão
    # contra o Postgres do container (pool de conexões de verdade — 5 tentativas
    # x 5 threads, sempre idempotente, zero exceção). SQLite com StaticPool
    # compartilha 1 única conexão sqlite3 entre threads, que não é thread-safe
    # pra execução concorrente real (é limitação do driver, não do código) —
    # por isso este teste simula a colisão dentro do MESMO lote/chamada, que
    # exercita a mesma lógica de captura sem depender de threading no SQLite.
    eng = _engine_teste()
    ponto = _dt(11), 0.96
    # 2 pontos idênticos no mesmo lote: a 2ª ocorrência colide com a 1ª
    # (que já foi inserida e commitada via savepoint na mesma chamada).
    n = salvar_precos(eng, "colisao-test", [ponto, ponto])
    assert n == 1  # só a 1ª conta; a 2ª colide e é descartada sem exceção
    assert len(ler_serie_precos(eng, "colisao-test")) == 1


def test_precos_separados_por_ativo():
    eng = _engine_teste()
    salvar_precos(eng, "usd-coin", [(_dt(11), 0.96)])
    salvar_precos(eng, "tether", [(_dt(11), 0.998)])
    assert len(ler_serie_precos(eng, "usd-coin")) == 1
    assert len(ler_serie_precos(eng, "tether")) == 1


def test_salvar_e_ler_risco():
    eng = _engine_teste()
    salvar_risk_snapshot(eng, "usd-coin", _dt(11), es=0.0176, var=0.006, faixa="baixo", teto=0.60)
    serie = ler_serie_risco(eng, "usd-coin")
    assert len(serie) == 1
    assert serie[0]["faixa"] == "baixo"
    assert abs(serie[0]["es"] - 0.0176) < 1e-9