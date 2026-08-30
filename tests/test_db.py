try:
    from src.db import get_engine
except ImportError:
    from db import get_engine


def test_engine_verifica_conexao_antes_de_reutilizar_pool():
    engine = get_engine("sqlite://")

    assert engine.pool._pre_ping is True
