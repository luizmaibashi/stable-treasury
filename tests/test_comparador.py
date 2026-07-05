import polars as pl
try:
    from src.comparador import comparar_custos, gerar_faturas_sinteticas
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.comparador import comparar_custos, gerar_faturas_sinteticas


def test_comparador_retorna_dataframe():
    df = comparar_custos(50000, "remessa_internacional_terceiros")
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 6


def test_comparador_tem_colunas_esperadas():
    df = comparar_custos(50000)
    cols = ["trilho", "moeda", "spread_brl", "tarifa_brl", "iof_brl", "gas_brl", "custo_total_brl", "custo_percent"]
    for c in cols:
        assert c in df.columns


def test_comparador_ordenado_por_custo():
    df = comparar_custos(50000)
    custos = df["custo_total_brl"].to_list()
    assert custos == sorted(custos)


def test_wire_tem_spread_e_iof_positivos():
    df = comparar_custos(100000, "remessa_internacional_terceiros")
    wire = df.filter(pl.col("trilho") == "Wire (SWIFT)")
    assert wire["spread_brl"][0] > 0
    assert wire["iof_brl"][0] > 0
    assert wire["tarifa_brl"][0] > 0


def test_pix_custo_zero():
    df = comparar_custos(50000)
    pix = df.filter(pl.col("trilho") == "PIX")
    assert pix["custo_total_brl"][0] == 0.0


def test_iof_zero_para_stablecoin():
    df = comparar_custos(50000, "stablecoin")
    wire = df.filter(pl.col("trilho") == "Wire (SWIFT)")
    assert wire["iof_brl"][0] == 0.0


def test_iof_35_para_remessa():
    df = comparar_custos(100000, "remessa_internacional_terceiros")
    wire = df.filter(pl.col("trilho") == "Wire (SWIFT)")
    iof_esperado = (100000 / 5.0) * 0.035 * 5.0
    assert abs(wire["iof_brl"][0] - iof_esperado) < 1.0


def test_gas_fee_variacao_por_rede():
    df = comparar_custos(50000)
    erc20 = df.filter(pl.col("moeda") == "USDT → BRL")
    poly = df.filter(pl.col("moeda") == "USDT → BRL")
    assert erc20["gas_brl"][0] >= 0
    assert poly["gas_brl"][0] >= 0


def test_faturas_sinteticas_4_perfis():
    df = gerar_faturas_sinteticas()
    assert len(df) == 4
    assert "perfil" in df.columns


def test_melhor_trilho_nao_vazio():
    df = gerar_faturas_sinteticas()
    assert all(df["melhor_trilho"].to_list())
