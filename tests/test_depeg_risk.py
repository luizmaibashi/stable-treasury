from datetime import timezone

import numpy as np
try:
    from src.depeg_risk import (
        var_es_historico, historico_preco_peg, historico_pontos_peg,
        desvio_peg, classificar_risco_e_teto, avaliar_risco_atual,
    )
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.depeg_risk import (
        var_es_historico, historico_preco_peg, historico_pontos_peg,
        desvio_peg, classificar_risco_e_teto, avaliar_risco_atual,
    )


def test_var_es_captura_cauda_que_var_sozinho_perde():
    # 8 dias normais + 2 dias ruins: -10% (choque "USDC-like") e -50% (choque "UST-like")
    retornos = np.array([0.0] * 8 + [-0.1, -0.5])
    var, es = var_es_historico(retornos, confianca=0.8)
    # confiança 0.8, n=10 -> tail de 2 piores casos (20%). VaR = fronteira do pior 2, ou seja o "menos ruim" deles: 10%
    assert var == 0.1
    # ES = média dos 2 piores (10% e 50%) = 30% -> maior que o VaR, porque enxerga o choque de -50% que o VaR sozinho esconde
    assert es == 0.3


def test_var_es_historico_com_array_vazio_levanta_erro_claro():
    # PAVC audit: array vazio quebrava com IndexError obscuro. Deve falhar
    # alto e claro (ValueError) — nunca retornar (0,0), que mentiria "risco zero"
    # quando na verdade é "sem dado pra concluir nada".
    import pytest
    with pytest.raises(ValueError, match="vazio"):
        var_es_historico(np.array([]), confianca=0.97)


def test_sem_choque_var_e_es_sao_zero():
    retornos = np.array([0.0] * 10)
    var, es = var_es_historico(retornos, confianca=0.9)
    assert var == 0.0
    assert es == 0.0


def test_historico_preco_peg_cobre_evento_usdc_svb():
    # janela real já verificada ao vivo: USDC caiu a ~0.8767 em 11/mar/2023 (evento SVB)
    inicio_svb = 1678406400  # 2023-03-10 00:00 UTC
    precos = historico_preco_peg("usd-coin", inicio_svb, dias=6)
    assert len(precos) > 0
    # granularidade diária amostra 1 ponto/dia, então não pega o mínimo intra-dia
    # exato (0.8767, que é hourly) — mas a queda real do evento tem que aparecer
    assert min(precos) < 0.97


def test_historico_pontos_peg_retorna_ts_e_preco():
    inicio_svb = 1678406400  # 2023-03-10 00:00 UTC
    pontos = historico_pontos_peg("usd-coin", inicio_svb, dias=6)
    assert len(pontos) > 0
    ts, price = pontos[0]
    assert ts.tzinfo is not None                 # datetime tz-aware (UTC)
    assert ts.tzinfo == timezone.utc
    assert isinstance(price, float)
    assert min(p for _, p in pontos) < 0.97      # a queda real do evento aparece


def test_desvio_peg_e_diferenca_direta_de_1():
    precos = [1.00, 0.96, 1.02]
    desvios = desvio_peg(precos)
    assert abs(desvios[0] - 0.0) < 1e-9
    assert abs(desvios[1] - (-0.04)) < 1e-9
    assert abs(desvios[2] - 0.02) < 1e-9


def test_classificar_risco_baixo():
    faixa, teto = classificar_risco_e_teto(es=0.0176)  # ES real do evento USDC-SVB
    assert faixa == "baixo"
    assert teto == 0.60


def test_classificar_risco_alto():
    faixa, teto = classificar_risco_e_teto(es=0.9932)  # ES real do evento UST
    assert faixa == "alto"
    assert teto == 0.10


def test_classificar_risco_medio_fronteira():
    faixa, teto = classificar_risco_e_teto(es=0.05)  # exatamente na fronteira baixo/médio
    assert faixa == "medio"
    assert teto == 0.30


def test_avaliar_risco_atual_usdc_retorna_faixa_valida():
    # pipeline completo com dado real recente: fetch -> desvio -> VaR/ES -> classificação
    faixa, teto, es = avaliar_risco_atual("usd-coin", dias=90)
    assert faixa in ("baixo", "medio", "alto")
    assert 0.0 < teto <= 0.60
    assert es >= 0.0