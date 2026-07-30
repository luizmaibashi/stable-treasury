# Compliance Filter: implementação determinística das resoluções BCB
# BCB 519 (ativos virtuais como valores mobiliários)
# BCB 520 (custódia e KYC)
# BCB 521 (segregação patrimonial)
# BCB 561 (proibição de ativos virtuais em eFX - vigência: 1º out/2026)

# NOTA: Estas são regras codificadas a partir do texto público das resoluções.
# Não constituem assessoria jurídica. Consulte um advogado para compliance real.

MOEDAS_STABLECOIN = {"USDT", "USDC", "DAI", "BUSD", "TUSD"}


def validar_transacao(transacao: dict) -> dict:
    tipo = transacao.get("tipo", "remessa_internacional_terceiros")
    moeda_saida = transacao.get("moeda_saida", "USD")
    trilho = transacao.get("trilho", "wire")
    valor_brl = transacao.get("valor_brl", 0)
    kyc_completo = transacao.get("kyc_completo", False)

    erros = []
    avisos = []
    permitido = True
    # Achado menor (auditoria 2026-07-30): antes retornava sempre as mesmas 3 resoluções,
    # independente da transação avaliada. Agora só entra aqui a resolução que REALMENTE
    # disparou (erro ou aviso) nesta transação — reflete o que foi de fato avaliado.
    resolucoes_aplicadas = []

    if trilho in ("USDT", "USDC") and tipo == "eletronico_cambio":
        erros.append("BCB 561: ativo virtual proibido como trilho de liquidação em eFX (Res. 561, vigência: 1º out/2026)")
        permitido = False
        resolucoes_aplicadas.append("BCB 561")

    if moeda_saida in MOEDAS_STABLECOIN and not kyc_completo:
        avisos.append("BCB 520: KYC obrigatório para transações com ativos virtuais")
        resolucoes_aplicadas.append("BCB 520")

    if valor_brl > 500000:
        avisos.append(f"Valor acima de R$500k ({valor_brl:,.0f}): declarar ao BCB via e-DRS (Res. 521)")
        resolucoes_aplicadas.append("BCB 521")

    return {
        "transacao_id": transacao.get("id", "unknown"),
        "permitido": permitido,
        "erros": erros,
        "avisos": avisos,
        "resolucoes_aplicadas": resolucoes_aplicadas,
    }


def filtrar_trilhos_permitidos(trilhos: list[str], tipo_operacao: str) -> list[str]:
    if tipo_operacao == "eletronico_cambio":
        return [t for t in trilhos if t not in ("USDT", "USDC")]
    return trilhos
