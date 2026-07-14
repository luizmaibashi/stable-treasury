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


def test_importacao_bens_isenta():
    # Decreto 6.306 Art. 15-B §1º: câmbio de importação de bens é ISENTO (ADR-0011)
    assert aliquota_iof("importacao_bens") == 0.0


def test_importacao_servicos_038():
    assert aliquota_iof("importacao_servicos") == 0.38


def test_economia_stablecoin_menor_quando_iof_isento():
    # a arbitragem do stablecoin encolhe onde o IOF já é isento (importação de bens),
    # e é máxima onde o IOF é alto (remessa/serviços 3,5%) — ADR-0011
    import polars as pl
    from src.comparador import comparar_custos
    remessa = comparar_custos(100000, "remessa_internacional_terceiros", caso_uso="cross_border")
    importacao = comparar_custos(100000, "importacao_bens", caso_uso="cross_border")
    wire_remessa = remessa.filter(pl.col("trilho") == "Wire (SWIFT)")["custo_total_brl"][0]
    wire_importacao = importacao.filter(pl.col("trilho") == "Wire (SWIFT)")["custo_total_brl"][0]
    # sem IOF, o Wire fica muito mais barato -> a vantagem do stablecoin diminui
    assert wire_importacao < wire_remessa
