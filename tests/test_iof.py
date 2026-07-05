try:
    from src.iof_tabela import carregar_iof, aliquota_iof
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.iof_tabela import carregar_iof, aliquota_iof


def test_carrega_iof():
    tabela = carregar_iof()
    assert len(tabela) >= 5


def test_aliquota_remessa():
    assert aliquota_iof("remessa_internacional_terceiros") == 3.5


def test_aliquota_investimento():
    assert aliquota_iof("investimento_exterior") == 1.1


def test_aliquota_entrada():
    assert aliquota_iof("entrada_recursos_exterior") == 0.38


def test_aliquota_stablecoin():
    assert aliquota_iof("stablecoin") == 0.0


def test_tipo_desconhecido_retorna_zero():
    assert aliquota_iof("tipo_inexistente") == 0.0
