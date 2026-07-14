try:
    from src.otimizador import otimizar_alocacao
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.otimizador import otimizar_alocacao


# --- detecção de perfil ---

def test_exportador_detectado():
    res = otimizar_alocacao(
        saldo_brl=500000, saldo_usdt=10000, saldo_usd=5000,
        previsao_gasto_brl_30d=150000, previsao_recebimento_usd_30d=20000,
        previsao_pagamento_usd_30d=30000,
    )
    assert res["exportador"] is True


# --- reserva em CASH, dimensionada por DCOH (ADR-0009) ---

def test_reserva_gap_quando_caixa_abaixo_do_dcoh():
    # DCOH default 60 dias = 2 meses. gasto 50k -> reserva necessária 100k.
    res = otimizar_alocacao(
        saldo_brl=50000, saldo_usdt=0, saldo_usd=0,
        previsao_gasto_brl_30d=50000, previsao_recebimento_usd_30d=0,
    )
    assert res["meses_reserva_brl"] == 1.0
    assert res["converter_usdt_para_brl"] > 0  # falta cash pra reserva


def test_reserva_confortavel_sem_gap():
    res = otimizar_alocacao(
        saldo_brl=500000, saldo_usdt=0, saldo_usd=0,
        previsao_gasto_brl_30d=50000, previsao_recebimento_usd_30d=0,
    )
    assert res["converter_usdt_para_brl"] == 0


def test_stablecoin_nunca_invade_a_reserva():
    # reserva em cash (BRL) tem prioridade; stablecoin não pode empurrar BRL abaixo do piso
    res = otimizar_alocacao(
        saldo_brl=200000, saldo_usdt=0, saldo_usd=0,
        previsao_gasto_brl_30d=80000, previsao_recebimento_usd_30d=0,
        previsao_pagamento_usd_30d=1_000_000,  # fluxo enorme tentando puxar stablecoin
        teto_stablecoin=0.60,
    )
    total = res["saldo_total_equivalent_brl"]
    reserva_frac = min(1.0, (80000 * 2) / total)  # DCOH 60d = 2 meses
    assert res["alocacao_pct"]["BRL"] >= reserva_frac - 1e-6


# --- stablecoin = working capital, com teto triplo (ADR-0009) ---

def test_stablecoin_zero_sem_fluxo_cross_border():
    # sem pagamento cross-border não há giro no trilho -> stablecoin = 0
    res = otimizar_alocacao(
        saldo_brl=500000, saldo_usdt=0, saldo_usd=0,
        previsao_gasto_brl_30d=50000, previsao_recebimento_usd_30d=0,
        previsao_pagamento_usd_30d=0,
        teto_stablecoin=0.60,
    )
    assert res["alocacao_pct"]["stablecoin"] == 0.0


def test_stablecoin_respeita_cap_de_politica():
    # fluxo grande + risco baixo (teto 60%): o cap de política (5%) tem que morder
    res = otimizar_alocacao(
        saldo_brl=10_000_000, saldo_usdt=0, saldo_usd=0,
        previsao_gasto_brl_30d=100000, previsao_recebimento_usd_30d=0,
        previsao_pagamento_usd_30d=5_000_000,
        teto_stablecoin=0.60, cap_politica_stablecoin=0.05,
    )
    assert res["alocacao_pct"]["stablecoin"] <= 0.05 + 1e-6


def test_stablecoin_respeita_teto_de_depeg():
    # teto de depeg (2%) mais restritivo que a política (5%) -> depeg manda
    res = otimizar_alocacao(
        saldo_brl=10_000_000, saldo_usdt=0, saldo_usd=0,
        previsao_gasto_brl_30d=100000, previsao_recebimento_usd_30d=0,
        previsao_pagamento_usd_30d=5_000_000,
        teto_stablecoin=0.02, cap_politica_stablecoin=0.05,
    )
    assert res["alocacao_pct"]["stablecoin"] <= 0.02 + 1e-6


# --- coerência global ---

def test_alocacao_soma_um():
    res = otimizar_alocacao(
        saldo_brl=1_000_000, saldo_usdt=50000, saldo_usd=20000,
        previsao_gasto_brl_30d=100000, previsao_recebimento_usd_30d=40000,
        previsao_pagamento_usd_30d=200000,
        teto_stablecoin=0.30,
    )
    assert abs(sum(res["alocacao_pct"].values()) - 1.0) < 1e-6


def test_haircut_es_reduz_valor_de_liquidez_da_stablecoin():
    # o valor de liquidez da stablecoin é descontado pelo ES (haircut, ADR-0009)
    base = dict(
        saldo_brl=5_000_000, saldo_usdt=0, saldo_usd=0,
        previsao_gasto_brl_30d=100000, previsao_recebimento_usd_30d=0,
        previsao_pagamento_usd_30d=2_000_000, teto_stablecoin=0.30,
    )
    sem_risco = otimizar_alocacao(**base, es_stablecoin=0.0)
    com_risco = otimizar_alocacao(**base, es_stablecoin=0.20)
    assert com_risco["valor_liquidez_stablecoin_brl"] < sem_risco["valor_liquidez_stablecoin_brl"]


def test_exportador_mantem_excedente_em_usd():
    res = otimizar_alocacao(
        saldo_brl=1_000_000, saldo_usdt=0, saldo_usd=0,
        previsao_gasto_brl_30d=50000, previsao_recebimento_usd_30d=100000,
        previsao_pagamento_usd_30d=0,
    )
    assert res["alocacao_pct"]["USD"] > 0