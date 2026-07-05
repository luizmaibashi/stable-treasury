from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

try:
    from src.ingestao import janelas_paginacao, gerar_snapshots_risco_historico
    from src.db import init_schema
    from src.repositorio import salvar_precos, ler_serie_risco
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.ingestao import janelas_paginacao, gerar_snapshots_risco_historico
    from src.db import init_schema
    from src.repositorio import salvar_precos, ler_serie_risco


def _engine_teste():
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    init_schema(eng)
    return eng


def test_janela_unica_quando_periodo_menor_que_chunk():
    # 100 dias, chunk 450 -> 1 janela só
    janelas = janelas_paginacao(inicio_unix=1000, fim_unix=1000 + 100 * 86400, chunk_dias=450)
    assert len(janelas) == 1
    assert janelas[0][0] == 1000


def test_pagina_periodo_longo_em_multiplas_janelas():
    # ~1000 dias, chunk 450 -> 3 janelas (450 + 450 + resto), cobrindo o período todo
    inicio = 1_640_995_200  # 2022-01-01
    fim = inicio + 1000 * 86400
    janelas = janelas_paginacao(inicio_unix=inicio, fim_unix=fim, chunk_dias=450)
    assert len(janelas) == 3
    assert janelas[0][0] == inicio                      # começa no início
    # cada janela avança 450 dias a partir da anterior
    assert janelas[1][0] == inicio + 450 * 86400
    assert janelas[2][0] == inicio + 900 * 86400
    # nenhum span passa do limite seguro da DefiLlama (500)
    assert all(dias <= 500 for _, dias in janelas)


def test_snapshots_capturam_depeg_com_es_elevado():
    eng = _engine_teste()
    base = datetime(2023, 1, 1, tzinfo=timezone.utc)
    # 120 dias no peg (1.00) seguidos de 10 dias de depeg severo (0.90)
    pontos = [(base + timedelta(days=i), 1.00) for i in range(120)]
    pontos += [(base + timedelta(days=120 + i), 0.90) for i in range(10)]
    salvar_precos(eng, "usd-coin", pontos)

    gerar_snapshots_risco_historico(eng, "usd-coin", janela_dias=90, passo_dias=15)
    serie = ler_serie_risco(eng, "usd-coin")

    assert len(serie) > 0
    es_values = [s["es"] for s in serie]
    # o pior ES da série (janela que inclui o depeg) tem que superar o ES em período calmo
    assert max(es_values) > 0.05        # depeg de 0.10 aparece como perda relevante
    assert min(es_values) < 0.01        # períodos totalmente no peg têm ES ~0