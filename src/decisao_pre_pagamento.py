"""Motor determinístico do pacote de decisão pré-pagamento.

Não consulta mercado nem executa pagamentos: a recomendação só organiza as
cotações e premissas informadas pelo responsável financeiro.
"""

from datetime import date, datetime, timezone


def avaliar_decisao_pre_pagamento(
    fatura: dict,
    cotacoes: list[dict],
    contexto: dict,
    politica: dict,
    *,
    agora: datetime | None = None,
) -> dict:
    """Compara cotações declaradas e retorna uma decisão condicionada.

    Timezone é obrigatório nas cotações para não mascarar idade de dado. Valores
    fora do domínio levantam erro; ausência de informação vira ``INCOMPLETO``.
    """
    agora = agora or datetime.now(timezone.utc)
    _validar_datetime_aware(agora, "agora")

    campos_ausentes = _campos_ausentes(fatura, cotacoes, contexto, politica)
    if campos_ausentes:
        return _resultado_incompleto(campos_ausentes)

    _validar_dominios(fatura, cotacoes, contexto, politica)

    alternativas = sorted(
        [_calcular_alternativa(fatura, cotacao, contexto) for cotacao in cotacoes],
        key=lambda alternativa: alternativa["custo_total_brl"],
    )
    exposicao = (
        contexto["recebimentos_usd_30d"]
        - contexto["pagamentos_usd_30d"]
        - fatura["valor_usd"]
    )
    alertas = _gerar_alertas(alternativas, fatura, politica, exposicao, agora)
    status = "REVISAR" if alertas else "PRONTO_PARA_APROVACAO"
    recomendacao = (
        None
        if status == "REVISAR"
        else f"Selecionar {alternativas[0]['parceiro']}, condicionado à aprovação humana."
    )
    return {
        "status": status,
        "alternativas": alternativas,
        "exposicao_liquida_usd_30d": exposicao,
        "alertas": alertas,
        "campos_ausentes": [],
        "recomendacao": recomendacao,
    }


def _campos_ausentes(fatura: dict, cotacoes: list[dict], contexto: dict, politica: dict) -> list[str]:
    faltantes = []
    for campo in ("id", "fornecedor", "valor_usd", "vencimento", "tipo_operacao"):
        if fatura.get(campo) in (None, ""):
            faltantes.append(f"Fatura: {campo}.")
    for campo in ("caixa_brl", "recebimentos_usd_30d", "pagamentos_usd_30d"):
        if contexto.get(campo) is None:
            faltantes.append(f"Contexto: {campo}.")
    for campo in ("custo_max_pct", "prazo_max_dias", "alcada_max_brl", "max_idade_cotacao_horas"):
        if politica.get(campo) is None:
            faltantes.append(f"Política: {campo}.")
    if len(cotacoes) < 2:
        faltantes.append("Ao menos duas cotações válidas são necessárias.")
    for indice, cotacao in enumerate(cotacoes, start=1):
        for campo in ("parceiro", "taxa_usd_brl", "tarifa_brl", "prazo_settlement_dias", "timestamp", "fonte"):
            if cotacao.get(campo) in (None, ""):
                faltantes.append(f"Cotação {indice}: {campo}.")
    return faltantes


def _validar_dominios(fatura: dict, cotacoes: list[dict], contexto: dict, politica: dict) -> None:
    _validar_numero_positivo(fatura["valor_usd"], "valor_usd")
    if not isinstance(fatura["vencimento"], date):
        raise ValueError("vencimento deve ser date")
    for campo in ("caixa_brl", "recebimentos_usd_30d", "pagamentos_usd_30d"):
        _validar_numero_nao_negativo(contexto[campo], campo)
    _validar_numero_nao_negativo(politica["custo_max_pct"], "custo_max_pct")
    _validar_numero_nao_negativo(politica["prazo_max_dias"], "prazo_max_dias")
    _validar_numero_positivo(politica["alcada_max_brl"], "alcada_max_brl")
    _validar_numero_nao_negativo(politica["max_idade_cotacao_horas"], "max_idade_cotacao_horas")
    for cotacao in cotacoes:
        _validar_numero_positivo(cotacao["taxa_usd_brl"], "taxa_usd_brl")
        _validar_numero_nao_negativo(cotacao["tarifa_brl"], "tarifa_brl")
        _validar_numero_nao_negativo(cotacao["prazo_settlement_dias"], "prazo_settlement_dias")
        _validar_datetime_aware(cotacao["timestamp"], "timestamp")


def _validar_numero_positivo(valor: float, nome: str) -> None:
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor <= 0:
        raise ValueError(f"{nome} deve ser número positivo")


def _validar_numero_nao_negativo(valor: float, nome: str) -> None:
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor < 0:
        raise ValueError(f"{nome} deve ser número não negativo")


def _validar_datetime_aware(valor: datetime, nome: str) -> None:
    if not isinstance(valor, datetime) or valor.tzinfo is None or valor.utcoffset() is None:
        raise ValueError(f"{nome} deve ter timezone explícito")


def _calcular_alternativa(fatura: dict, cotacao: dict, contexto: dict) -> dict:
    principal = fatura["valor_usd"] * cotacao["taxa_usd_brl"]
    total = principal + cotacao["tarifa_brl"]
    return {
        "parceiro": cotacao["parceiro"],
        "taxa_usd_brl": cotacao["taxa_usd_brl"],
        "tarifa_brl": cotacao["tarifa_brl"],
        "prazo_settlement_dias": cotacao["prazo_settlement_dias"],
        "timestamp": cotacao["timestamp"],
        "fonte": cotacao["fonte"],
        "valor_principal_brl": round(principal, 2),
        "custo_total_brl": round(total, 2),
        "custo_percentual": round(cotacao["tarifa_brl"] / principal * 100, 4),
        "caixa_pos_pagamento_brl": round(contexto["caixa_brl"] - total, 2),
    }


def _gerar_alertas(
    alternativas: list[dict], fatura: dict, politica: dict, exposicao: float, agora: datetime,
) -> list[dict]:
    alertas = []
    for alternativa in alternativas:
        idade_horas = (agora - alternativa["timestamp"].astimezone(timezone.utc)).total_seconds() / 3600
        if idade_horas < 0:
            alertas.append({"codigo": "COTACAO_FUTURA", "parceiro": alternativa["parceiro"], "mensagem": "Timestamp da cotação está no futuro; valide o relógio ou a informação recebida."})
        if idade_horas > politica["max_idade_cotacao_horas"]:
            alertas.append({"codigo": "COTACAO_VENCIDA", "parceiro": alternativa["parceiro"], "mensagem": "Cotação excede a idade máxima da política."})
        if alternativa["custo_percentual"] > politica["custo_max_pct"]:
            alertas.append({"codigo": "CUSTO_ACIMA_POLITICA", "parceiro": alternativa["parceiro"], "mensagem": "Custo percentual excede o limite da política."})
        if alternativa["prazo_settlement_dias"] > politica["prazo_max_dias"]:
            alertas.append({"codigo": "PRAZO_ACIMA_POLITICA", "parceiro": alternativa["parceiro"], "mensagem": "Prazo de liquidação excede o limite da política."})
        if alternativa["caixa_pos_pagamento_brl"] < 0:
            alertas.append({"codigo": "CAIXA_INSUFICIENTE", "parceiro": alternativa["parceiro"], "mensagem": "O caixa declarado não cobre o custo total desta alternativa."})
    if min(alternativa["valor_principal_brl"] for alternativa in alternativas) > politica["alcada_max_brl"]:
        alertas.append({"codigo": "ALCADA_EXCEDIDA", "mensagem": "Valor principal excede a alçada configurada."})
    if exposicao < 0:
        alertas.append({"codigo": "EXPOSICAO_NEGATIVA", "mensagem": "A fatura deixa a exposição líquida em USD negativa."})
    return alertas


def _resultado_incompleto(campos_ausentes: list[str]) -> dict:
    return {
        "status": "INCOMPLETO",
        "alternativas": [],
        "exposicao_liquida_usd_30d": None,
        "alertas": [],
        "campos_ausentes": campos_ausentes,
        "recomendacao": None,
    }
