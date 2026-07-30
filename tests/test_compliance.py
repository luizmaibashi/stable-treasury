try:
    from src.compliance import validar_transacao, filtrar_trilhos_permitidos
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.compliance import validar_transacao, filtrar_trilhos_permitidos


def test_eFX_com_stablecoin_bloqueado():
    resultado = validar_transacao({
        "id": "T1",
        "tipo": "eletronico_cambio",
        "moeda_saida": "USDT",
        "trilho": "USDT",
        "valor_brl": 50000,
        "kyc_completo": True,
    })
    assert resultado["permitido"] is False
    assert any("561" in e for e in resultado["erros"])


def test_remessa_com_stablecoin_permitido():
    resultado = validar_transacao({
        "id": "T2",
        "tipo": "remessa_internacional",
        "moeda_saida": "USDT",
        "trilho": "USDT",
        "valor_brl": 50000,
        "kyc_completo": True,
    })
    assert resultado["permitido"] is True


def test_sem_kyc_gera_aviso():
    resultado = validar_transacao({
        "id": "T3",
        "tipo": "remessa_internacional",
        "moeda_saida": "USDT",
        "trilho": "USDT",
        "valor_brl": 50000,
        "kyc_completo": False,
    })
    assert any("KYC" in a for a in resultado["avisos"])


def test_valor_acima_500k_avisa():
    resultado = validar_transacao({
        "id": "T4",
        "tipo": "remessa_internacional",
        "moeda_saida": "USD",
        "trilho": "wire",
        "valor_brl": 600000,
        "kyc_completo": True,
    })
    assert any("500k" in a for a in resultado["avisos"])


# --- Achado menor (auditoria 2026-07-30): resolucoes_aplicadas retornava sempre as
# mesmas 3, independente da transação avaliada — não distinguia o que de fato disparou.

def test_resolucoes_aplicadas_reflete_o_que_disparou_nao_uma_lista_fixa():
    limpo = validar_transacao({
        "id": "T5", "tipo": "remessa_internacional", "moeda_saida": "USD",
        "trilho": "wire", "valor_brl": 1000, "kyc_completo": True,
    })
    assert limpo["resolucoes_aplicadas"] == []  # nenhuma regra disparou nesta transação

    so_kyc = validar_transacao({
        "id": "T6", "tipo": "remessa_internacional", "moeda_saida": "USDT",
        "trilho": "USDT", "valor_brl": 1000, "kyc_completo": False,
    })
    assert so_kyc["resolucoes_aplicadas"] == ["BCB 520"]

    bloqueado = validar_transacao({
        "id": "T7", "tipo": "eletronico_cambio", "moeda_saida": "USDT",
        "trilho": "USDT", "valor_brl": 600000, "kyc_completo": False,
    })
    assert set(bloqueado["resolucoes_aplicadas"]) == {"BCB 561", "BCB 520", "BCB 521"}


def test_filtrar_trilhos_eFX():
    permitidos = filtrar_trilhos_permitidos(
        ["wire", "PIX", "USDT", "USDC"],
        "eletronico_cambio",
    )
    assert "USDT" not in permitidos
    assert "USDC" not in permitidos
    assert "wire" in permitidos
