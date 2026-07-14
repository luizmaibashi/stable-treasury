try:
    from src.custo_carrego import custo_carrego, custo_oportunidade_reserva
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.custo_carrego import custo_carrego, custo_oportunidade_reserva


# --- custo de carrego: matemática pura (ADR-0010) ---

def test_custo_carrego_gap_entre_taxa_e_yield_atual():
    # R$ 300M parados, CDI 14,15%, conta não remunerada (0%) -> gap = 14,15% do valor
    r = custo_carrego(valor_parado=300_000_000, taxa_referencia_pct=14.15, yield_atual_pct=0.0)
    assert abs(r["gap_anual"] - 42_450_000) < 1.0
    assert abs(r["gap_diario"] - 42_450_000 / 365) < 1.0


def test_custo_carrego_zero_quando_ja_remunerado_na_taxa():
    # se o caixa já rende o CDI, não há dinheiro na mesa
    r = custo_carrego(valor_parado=300_000_000, taxa_referencia_pct=14.15, yield_atual_pct=14.15)
    assert r["gap_anual"] == 0.0


def test_custo_carrego_nunca_negativo():
    # se o caixa rende MAIS que a referência, o gap é 0 (não é "lucro de oportunidade")
    r = custo_carrego(valor_parado=100_000, taxa_referencia_pct=5.0, yield_atual_pct=9.0)
    assert r["gap_anual"] == 0.0


def test_custo_carrego_cresce_com_a_taxa():
    baixo = custo_carrego(valor_parado=1_000_000, taxa_referencia_pct=5.0)
    alto = custo_carrego(valor_parado=1_000_000, taxa_referencia_pct=15.0)
    assert alto["gap_anual"] > baixo["gap_anual"]


# --- reserva completa: BRL (CDI) + USD (T-bill) ---

def test_custo_oportunidade_reserva_soma_brl_e_usd():
    r = custo_oportunidade_reserva(
        reserva_brl=300_000_000,
        posicao_usd=30_000_000,
        ptax=5.5,
        cdi_pct=14.15,
        tbill_pct=3.7,
        yield_atual_pct=0.0,
    )
    # BRL: 300M * 14,15% ; USD: 30M * 3,7% convertido a BRL pela PTAX
    esperado_brl = 300_000_000 * 0.1415
    esperado_usd_brl = 30_000_000 * 0.037 * 5.5
    assert abs(r["gap_brl_anual"] - esperado_brl) < 1.0
    assert abs(r["gap_usd_anual_brl"] - esperado_usd_brl) < 1.0
    assert abs(r["gap_total_anual_brl"] - (esperado_brl + esperado_usd_brl)) < 1.0


def test_custo_oportunidade_zero_sem_caixa():
    r = custo_oportunidade_reserva(
        reserva_brl=0, posicao_usd=0, ptax=5.5, cdi_pct=14.15, tbill_pct=3.7,
    )
    assert r["gap_total_anual_brl"] == 0.0
