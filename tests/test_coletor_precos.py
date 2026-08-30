try:
    from src.coletor_precos import (
        taxa_cdi, taxa_tbill, ptax_venda, TTL_TAXAS_SEGUNDOS,
        gas_fee_polygon_com_status, POLYGON_GAS_FALLBACK,
    )
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.coletor_precos import (
        taxa_cdi, taxa_tbill, ptax_venda, TTL_TAXAS_SEGUNDOS,
        gas_fee_polygon_com_status, POLYGON_GAS_FALLBACK,
    )


def test_gas_polygon_expoe_status_e_log_quando_usa_fallback(monkeypatch, caplog):
    import src.coletor_precos as cp

    def _falha_de_rede(*args, **kwargs):
        raise cp.requests.RequestException("fonte indisponível")

    monkeypatch.setattr(cp.requests, "get", _falha_de_rede)

    gas, em_fallback = gas_fee_polygon_com_status()

    assert em_fallback is True
    assert gas == POLYGON_GAS_FALLBACK
    assert "fallback_ativado fonte=PolygonScan" in caplog.text


def test_gas_polygon_resposta_sem_taxa_valida_ativa_fallback(monkeypatch):
    import src.coletor_precos as cp

    class _RespostaSemTaxa:
        def raise_for_status(self):
            pass

        def json(self):
            return {"status": "1", "result": {"ProposeGasPrice": "0"}}

    monkeypatch.setattr(cp.requests, "get", lambda *args, **kwargs: _RespostaSemTaxa())

    gas, em_fallback = gas_fee_polygon_com_status()

    assert em_fallback is True
    assert gas == POLYGON_GAS_FALLBACK


# --- Achado menor (auditoria 2026-07-30): lru_cache sem TTL em processo Streamlit de longa
# duração congela a taxa pra sempre na primeira consulta. Precisa expirar depois de um tempo.

def test_taxa_cdi_expira_apos_ttl(monkeypatch):
    import src.coletor_precos as cp
    chamadas = {"n": 0}

    def _resp_fake(*a, **k):
        chamadas["n"] += 1
        class _R:
            def raise_for_status(self):
                pass
            def json(self):
                return [{"valor": str(10.0 + chamadas["n"])}]
        return _R()

    monkeypatch.setattr(cp.requests, "get", _resp_fake)

    relogio = {"t": 1_000_000.0}
    monkeypatch.setattr(cp.time, "time", lambda: relogio["t"])

    cp.taxa_cdi.cache_clear()
    primeiro = taxa_cdi()
    segundo = taxa_cdi()  # mesmo instante -> cache hit, não bate na rede de novo
    assert primeiro == segundo
    assert chamadas["n"] == 1

    relogio["t"] += TTL_TAXAS_SEGUNDOS + 1  # avança além do TTL
    terceiro = taxa_cdi()
    assert chamadas["n"] == 2       # expirou -> nova chamada de rede
    assert terceiro != primeiro     # valor novo (fake incrementa a cada chamada)


def test_taxa_tbill_expira_apos_ttl(monkeypatch):
    import src.coletor_precos as cp
    chamadas = {"n": 0}

    def _resp_fake(*a, **k):
        chamadas["n"] += 1
        class _R:
            def raise_for_status(self):
                pass
            def json(self):
                return {"data": [{"avg_interest_rate_amt": str(3.0 + chamadas["n"])}]}
        return _R()

    monkeypatch.setattr(cp.requests, "get", _resp_fake)
    relogio = {"t": 2_000_000.0}
    monkeypatch.setattr(cp.time, "time", lambda: relogio["t"])

    cp.taxa_tbill.cache_clear()
    primeiro = taxa_tbill()
    assert taxa_tbill() == primeiro
    assert chamadas["n"] == 1

    relogio["t"] += TTL_TAXAS_SEGUNDOS + 1
    assert taxa_tbill() != primeiro
    assert chamadas["n"] == 2


def test_ptax_venda_expira_apos_ttl(monkeypatch):
    import src.coletor_precos as cp
    chamadas = {"n": 0}

    def _resp_fake(*a, **k):
        chamadas["n"] += 1
        class _R:
            def raise_for_status(self):
                pass
            def json(self):
                return [{"valor": str(5.5 + chamadas["n"])}]
        return _R()

    monkeypatch.setattr(cp.requests, "get", _resp_fake)
    relogio = {"t": 3_000_000.0}
    monkeypatch.setattr(cp.time, "time", lambda: relogio["t"])

    cp.ptax_venda.cache_clear()
    primeiro = ptax_venda()
    assert ptax_venda() == primeiro
    assert chamadas["n"] == 1

    relogio["t"] += TTL_TAXAS_SEGUNDOS + 1
    assert ptax_venda() != primeiro
    assert chamadas["n"] == 2
