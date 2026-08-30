from datetime import date, datetime, timedelta, timezone

import pytest

from src.decisao_pre_pagamento import avaliar_decisao_pre_pagamento


AGORA = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)


def _fatura(**sobrescritas):
    base = {
        "id": "FAT-001",
        "fornecedor": "Fornecedor Industrial Ltd.",
        "valor_usd": 100_000.0,
        "vencimento": date(2026, 9, 10),
        "tipo_operacao": "importacao_bens",
    }
    return base | sobrescritas


def _cotacoes(**sobrescritas):
    base = [
        {
            "parceiro": "Banco Alfa",
            "taxa_usd_brl": 5.20,
            "tarifa_brl": 2_000.0,
            "prazo_settlement_dias": 2,
            "timestamp": AGORA - timedelta(hours=2),
            "fonte": "E-mail comercial",
        },
        {
            "parceiro": "Corretora Beta",
            "taxa_usd_brl": 5.18,
            "tarifa_brl": 3_000.0,
            "prazo_settlement_dias": 1,
            "timestamp": AGORA - timedelta(hours=1),
            "fonte": "Portal do parceiro",
        },
    ]
    return sobrescritas.get("itens", base)


def _contexto(**sobrescritas):
    return {"caixa_brl": 800_000.0, "recebimentos_usd_30d": 20_000.0, "pagamentos_usd_30d": 40_000.0} | sobrescritas


def _politica(**sobrescritas):
    return {"custo_max_pct": 1.0, "prazo_max_dias": 3, "alcada_max_brl": 1_000_000.0, "max_idade_cotacao_horas": 24} | sobrescritas


def test_ordena_cotacoes_por_custo_total_e_fica_pronto_para_aprovacao():
    resultado = avaliar_decisao_pre_pagamento(
        _fatura(), _cotacoes(), _contexto(recebimentos_usd_30d=150_000.0), _politica(), agora=AGORA
    )
    assert resultado["status"] == "PRONTO_PARA_APROVACAO"
    assert resultado["alternativas"][0]["parceiro"] == "Corretora Beta"
    assert resultado["alternativas"][0]["custo_total_brl"] == 521_000.0
    assert resultado["recomendacao"] == "Selecionar Corretora Beta, condicionado à aprovação humana."


def test_calcula_exposicao_liquida_incluindo_a_fatura():
    resultado = avaliar_decisao_pre_pagamento(_fatura(), _cotacoes(), _contexto(), _politica(), agora=AGORA)
    assert resultado["exposicao_liquida_usd_30d"] == -120_000.0


def test_uma_cotacao_deixa_decisao_incompleta():
    resultado = avaliar_decisao_pre_pagamento(_fatura(), _cotacoes(itens=_cotacoes()[:1]), _contexto(), _politica(), agora=AGORA)
    assert resultado["status"] == "INCOMPLETO"
    assert "Ao menos duas cotações válidas são necessárias." in resultado["campos_ausentes"]


def test_cotacao_sem_timestamp_nao_gera_recomendacao():
    cotacoes = _cotacoes()
    cotacoes[0]["timestamp"] = None
    resultado = avaliar_decisao_pre_pagamento(_fatura(), cotacoes, _contexto(), _politica(), agora=AGORA)
    assert resultado["status"] == "INCOMPLETO"
    assert resultado["recomendacao"] is None


def test_cotacao_vencida_forca_revisar_com_mecanismo_explicito():
    cotacoes = _cotacoes()
    cotacoes[0]["timestamp"] = AGORA - timedelta(hours=25)
    resultado = avaliar_decisao_pre_pagamento(_fatura(), cotacoes, _contexto(), _politica(), agora=AGORA)
    assert resultado["status"] == "REVISAR"
    assert any(alerta["codigo"] == "COTACAO_VENCIDA" for alerta in resultado["alertas"])


def test_cotacao_futura_forca_revisar():
    cotacoes = _cotacoes()
    cotacoes[0]["timestamp"] = AGORA + timedelta(minutes=1)
    resultado = avaliar_decisao_pre_pagamento(_fatura(), cotacoes, _contexto(), _politica(), agora=AGORA)
    assert resultado["status"] == "REVISAR"
    assert any(alerta["codigo"] == "COTACAO_FUTURA" for alerta in resultado["alertas"])


def test_caixa_insuficiente_forca_revisar():
    resultado = avaliar_decisao_pre_pagamento(_fatura(), _cotacoes(), _contexto(caixa_brl=100_000.0), _politica(), agora=AGORA)
    assert resultado["status"] == "REVISAR"
    assert any(alerta["codigo"] == "CAIXA_INSUFICIENTE" for alerta in resultado["alertas"])


def test_custo_acima_da_politica_forca_revisar():
    resultado = avaliar_decisao_pre_pagamento(_fatura(), _cotacoes(), _contexto(), _politica(custo_max_pct=0.3), agora=AGORA)
    assert resultado["status"] == "REVISAR"
    assert any(alerta["codigo"] == "CUSTO_ACIMA_POLITICA" for alerta in resultado["alertas"])


def test_prazo_acima_da_politica_forca_revisar():
    resultado = avaliar_decisao_pre_pagamento(_fatura(), _cotacoes(), _contexto(), _politica(prazo_max_dias=1), agora=AGORA)
    assert resultado["status"] == "REVISAR"
    assert any(alerta["codigo"] == "PRAZO_ACIMA_POLITICA" for alerta in resultado["alertas"])


def test_fatura_acima_da_alcada_forca_revisar():
    resultado = avaliar_decisao_pre_pagamento(_fatura(valor_usd=250_000.0), _cotacoes(), _contexto(), _politica(alcada_max_brl=1_000_000.0), agora=AGORA)
    assert resultado["status"] == "REVISAR"
    assert any(alerta["codigo"] == "ALCADA_EXCEDIDA" for alerta in resultado["alertas"])


def test_exposicao_liquida_negativa_forca_revisar():
    resultado = avaliar_decisao_pre_pagamento(_fatura(), _cotacoes(), _contexto(), _politica(), agora=AGORA)
    assert resultado["status"] == "REVISAR"
    assert any(alerta["codigo"] == "EXPOSICAO_NEGATIVA" for alerta in resultado["alertas"])


def test_taxa_invalida_levanta_erro_em_vez_de_assumir_valor():
    cotacoes = _cotacoes()
    cotacoes[0]["taxa_usd_brl"] = 0.0
    with pytest.raises(ValueError, match="taxa_usd_brl"):
        avaliar_decisao_pre_pagamento(_fatura(), cotacoes, _contexto(), _politica(), agora=AGORA)


def test_timestamp_sem_timezone_levanta_erro_em_vez_de_assumir_utc():
    cotacoes = _cotacoes()
    cotacoes[0]["timestamp"] = datetime(2026, 8, 29, 10, 0)
    with pytest.raises(ValueError, match="timezone"):
        avaliar_decisao_pre_pagamento(_fatura(), cotacoes, _contexto(), _politica(), agora=AGORA)
