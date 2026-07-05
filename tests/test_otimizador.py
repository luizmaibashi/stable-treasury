try:
    from src.otimizador import otimizar_alocacao
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.otimizador import otimizar_alocacao


def test_exportador_detectado():
    res = otimizar_alocacao(
        saldo_brl=500000,
        saldo_usdt=10000,
        saldo_usd=5000,
        previsao_gasto_brl_30d=150000,
        previsao_recebimento_usd_30d=20000,
    )
    assert res["exportador"] is True


def test_reserva_baixa_recomenda_conversao():
    res = otimizar_alocacao(
        saldo_brl=100000,
        saldo_usdt=0,
        saldo_usd=0,
        previsao_gasto_brl_30d=50000,
        previsao_recebimento_usd_30d=0,
    )
    assert res["converter_usdt_para_brl"] > 0
    assert res["meses_reserva_brl"] == 2.0


def test_reserva_confortavel():
    res = otimizar_alocacao(
        saldo_brl=500000,
        saldo_usdt=0,
        saldo_usd=0,
        previsao_gasto_brl_30d=50000,
        previsao_recebimento_usd_30d=0,
    )
    assert res["meses_reserva_brl"] == 10.0
    assert res["converter_usdt_para_brl"] == 0


def test_teto_stablecoin_baixo_risco_nao_altera_alocacao_padrao():
    # faixa "baixo" (teto 60%) não restringe o exportador (padrão original já é 50%)
    res = otimizar_alocacao(
        saldo_brl=500000, saldo_usdt=10000, saldo_usd=5000,
        previsao_gasto_brl_30d=150000, previsao_recebimento_usd_30d=20000,
        faixa_risco_stablecoin="baixo", teto_stablecoin=0.60,
    )
    assert res["alocacao_stablecoin_pct"] == 0.50
    assert res["faixa_risco_stablecoin"] == "baixo"


def test_teto_stablecoin_alto_risco_reduz_alocacao_e_realoca_pra_brl():
    # faixa "alto" (teto 10%) tem que CAPAR os 50% originais do exportador em 10%,
    # e o que sobrou (40 pontos percentuais) vai pra BRL, não desaparece
    res = otimizar_alocacao(
        saldo_brl=500000, saldo_usdt=10000, saldo_usd=5000,
        previsao_gasto_brl_30d=150000, previsao_recebimento_usd_30d=20000,
        faixa_risco_stablecoin="alto", teto_stablecoin=0.10,
    )
    assert res["alocacao_stablecoin_pct"] == 0.10
    assert res["faixa_risco_stablecoin"] == "alto"
