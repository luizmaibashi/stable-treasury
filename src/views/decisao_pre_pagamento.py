from datetime import datetime, timezone

import streamlit as st

from src.decisao_pre_pagamento import avaliar_decisao_pre_pagamento
from src.ui import intro


def renderizar():
    st.header("Demonstração de decisão pré-pagamento")
    intro(
        "Veja como duas cotações declaradas podem gerar uma decisão revisável.",
        "Este cenário sintético compara custo, prazo, caixa e exposição cambial usando somente dados declarados "
        "— sem buscar cotação de mercado ou mover dinheiro.",
        "altere a fatura e as duas cotações para observar os estados fail-safe. O resultado não aprova uma "
        "operação: ele mostra o que ficaria pronto para aprovação humana e o que exigiria revisão.",
    )

    with st.form("decisao_pre_pagamento"):
        col_fatura, col_contexto = st.columns(2)
        with col_fatura:
            st.caption("01 · Fatura")
            id_fatura = st.text_input("Identificador da fatura", value="FAT-2026-001")
            fornecedor = st.text_input("Fornecedor", value="Fornecedor Industrial Ltd.")
            valor_usd = st.number_input("Valor da fatura (USD)", min_value=0.0, value=100_000.0, step=10_000.0)
            vencimento = st.date_input("Vencimento")
            tipo_operacao_decisao = st.selectbox("Tipo de operação", ["Importação de bens", "Importação de serviços", "Outro"])
        with col_contexto:
            st.caption("02 · Contexto e política")
            caixa_brl = st.number_input("Caixa BRL disponível", min_value=0.0, value=800_000.0, step=50_000.0)
            recebimentos_usd = st.number_input("Recebimentos USD (30d)", min_value=0.0, value=150_000.0, step=10_000.0)
            pagamentos_usd = st.number_input("Pagamentos USD já previstos (30d)", min_value=0.0, value=40_000.0, step=10_000.0)
            custo_max = st.number_input("Custo máximo da política (%)", min_value=0.0, value=1.0, step=0.1)
            prazo_max = st.number_input("Prazo máximo da política (dias)", min_value=0, value=3, step=1)
            alcada_max = st.number_input("Alçada máxima (BRL)", min_value=0.0, value=1_000_000.0, step=50_000.0)
            idade_max_cotacao = st.number_input("Validade máxima da cotação (horas)", min_value=0, value=24, step=1)

        st.divider()
        st.caption("03 · Cotações recebidas")
        col_a, col_b = st.columns(2)
        cotacoes_formulario = []
        agora_formulario = datetime.now(timezone.utc)
        for coluna, sufixo, parceiro_padrao, taxa_padrao, tarifa_padrao, prazo_padrao in [
            (col_a, "A", "Banco Alfa", 5.20, 2_000.0, 2),
            (col_b, "B", "Corretora Beta", 5.18, 3_000.0, 1),
        ]:
            with coluna:
                st.markdown(f"**Cotação {sufixo}**")
                parceiro = st.text_input("Parceiro", value=parceiro_padrao, key=f"parceiro_{sufixo}")
                taxa = st.number_input("Taxa USD/BRL", min_value=0.0, value=taxa_padrao, step=0.01, key=f"taxa_{sufixo}")
                tarifa = st.number_input("Tarifa (BRL)", min_value=0.0, value=tarifa_padrao, step=500.0, key=f"tarifa_{sufixo}")
                prazo = st.number_input("Prazo de liquidação (dias)", min_value=0, value=prazo_padrao, step=1, key=f"prazo_{sufixo}")
                data_cotacao = st.date_input("Data da cotação", value=agora_formulario.date(), key=f"data_{sufixo}")
                hora_cotacao = st.time_input("Horário da cotação (UTC)", value=agora_formulario.time().replace(microsecond=0), key=f"hora_{sufixo}")
                fonte = st.text_input("Fonte declarada", value="Cotação recebida do parceiro", key=f"fonte_{sufixo}")
                cotacoes_formulario.append({
                    "parceiro": parceiro,
                    "taxa_usd_brl": taxa,
                    "tarifa_brl": tarifa,
                    "prazo_settlement_dias": prazo,
                    "timestamp": datetime.combine(data_cotacao, hora_cotacao, tzinfo=timezone.utc),
                    "fonte": fonte,
                })

        gerar_dossie = st.form_submit_button("Gerar dossiê de decisão", type="primary")

    if gerar_dossie:
        resultado_decisao = avaliar_decisao_pre_pagamento(
            {
                "id": id_fatura,
                "fornecedor": fornecedor,
                "valor_usd": valor_usd,
                "vencimento": vencimento,
                "tipo_operacao": tipo_operacao_decisao,
            },
            cotacoes_formulario,
            {
                "caixa_brl": caixa_brl,
                "recebimentos_usd_30d": recebimentos_usd,
                "pagamentos_usd_30d": pagamentos_usd,
            },
            {
                "custo_max_pct": custo_max,
                "prazo_max_dias": prazo_max,
                "alcada_max_brl": alcada_max,
                "max_idade_cotacao_horas": idade_max_cotacao,
            },
        )
        st.session_state["resultado_decisao_pre_pagamento"] = resultado_decisao

    resultado_decisao = st.session_state.get("resultado_decisao_pre_pagamento")
    if resultado_decisao:
        estado = resultado_decisao["status"]
        if estado == "PRONTO_PARA_APROVACAO":
            st.success(f"{estado}: {resultado_decisao['recomendacao']}")
        elif estado == "REVISAR":
            st.warning("REVISAR: há condições que exigem análise humana antes de qualquer aprovação.")
        else:
            st.info("INCOMPLETO: o dossiê não recomenda uma alternativa enquanto faltarem dados.")

        if resultado_decisao["campos_ausentes"]:
            st.subheader("Informações necessárias")
            for campo in resultado_decisao["campos_ausentes"]:
                st.write(f"- {campo}")
        else:
            melhor = resultado_decisao["alternativas"][0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Menor custo total", f"R$ {melhor['custo_total_brl']:,.2f}")
            m2.metric("Prazo", f"{melhor['prazo_settlement_dias']} dias")
            m3.metric("Caixa após pagamento", f"R$ {melhor['caixa_pos_pagamento_brl']:,.2f}")
            m4.metric("Exposição líquida USD (30d)", f"US$ {resultado_decisao['exposicao_liquida_usd_30d']:,.0f}")
            st.subheader("Alternativas e premissas")
            st.dataframe(resultado_decisao["alternativas"], hide_index=True, width="stretch")
            if resultado_decisao["alertas"]:
                st.subheader("Pontos para revisão")
                for alerta in resultado_decisao["alertas"]:
                    parceiro_alerta = f" ({alerta['parceiro']})" if "parceiro" in alerta else ""
                    st.warning(f"{alerta['codigo']}{parceiro_alerta}: {alerta['mensagem']}")
            st.caption(
                "Este dossiê organiza dados declarados e regras internas. Não executa pagamento, não gera cotação "
                "e não constitui parecer jurídico, regulatório ou de investimento."
            )
