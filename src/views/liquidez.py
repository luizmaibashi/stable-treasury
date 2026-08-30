import streamlit as st

from src.custo_carrego import custo_oportunidade_reserva
from src.depeg_risk import avaliar_risco_carteira
from src.otimizador import otimizar_alocacao
from src.ui import intro


def renderizar():
    st.header("Otimizador de Liquidez")
    intro(
        "Como dividir o caixa da empresa entre real, dólar e dólar digital?",
        'Uma tesouraria precisa de <b>reserva de emergência</b> (sempre em dinheiro de verdade — stablecoin '
        'não conta como caixa pela regra contábil), pode manter <b>dólar</b> se tem contas em dólar (hedge '
        'natural), e usa <b>stablecoin</b> só como dinheiro em trânsito para pagar lá fora — nunca como '
        'investimento. O motor decide os percentuais respeitando essas regras e o risco de depeg.',
        'a frase de <b>alocação</b> mostra a divisão final. Repare: mesmo com risco baixo, a stablecoin fica '
        'em ~5% (limite de política, não de risco). E o <b>Custo de Oportunidade</b> mostra quanto a reserva '
        'parada deixa de render — dinheiro na mesa que dá pra capturar sem risco.',
    )

    col_l1, col_l2 = st.columns(2)
    with col_l1:
        saldo_brl = st.number_input("Saldo BRL", min_value=0, value=500000, step=10000)
        saldo_usdt = st.number_input("Saldo USDT", min_value=0.0, value=10000.0, step=1000.0)
        saldo_usd = st.number_input("Saldo USD", min_value=0.0, value=5000.0, step=1000.0)

    with col_l2:
        gasto_30d = st.number_input("Previsão gasto BRL (30d)", min_value=0, value=150000, step=10000)
        recebimento_30d = st.number_input("Previsão recebimento USD (30d)", min_value=0.0, value=20000.0, step=5000.0)
        pagamento_30d = st.number_input(
            "Previsão pagamento cross-border USD (30d)", min_value=0.0, value=200000.0, step=10000.0,
            help="Fluxo de pagamento a fornecedores/parceiros no exterior. Dimensiona o capital de giro em trânsito no trilho stablecoin (ADR-0009).",
        )
        yield_atual = st.number_input(
            "Rendimento atual do caixa (% a.a.)", min_value=0.0, max_value=30.0, value=0.0, step=0.5,
            help="Quanto sua reserva já rende hoje. O default (0%) é um CENÁRIO PIOR CASO — conta "
                 "totalmente não remunerada. Tesouraria de grande porte normalmente já captura parte "
                 "do CDI via sweep automático/fundo DI; ajuste para o seu caso real antes de tratar "
                 "o número abaixo como decisão (achado #7).",
        )
        pct_usdc = st.slider(
            "Composição stablecoin: % USDC (resto USDT)", min_value=0, max_value=100, value=50, step=5,
            help="O risco de depeg é medido sobre a CARTEIRA real (USDC+USDT ponderados), não só sobre USDC. A correlação entre os dois emerge do dado (ADR-0011, débito #7).",
        ) / 100

    if st.button("Otimizar alocação", type="primary"):
        with st.spinner("Avaliando risco de depeg da carteira (VaR/ES horário sobre USDC+USDT)..."):
            # risco medido sobre a CARTEIRA real (USDC+USDT ponderados), série horária —
            # correlação emerge do dado (ADR-0011, corrige débito #7). avaliar_risco_atual
            # (só USDC) segue disponível como fallback conceitual.
            faixa_risco, teto_risco, es_atual = avaliar_risco_carteira(
                {"usd-coin": pct_usdc, "tether": 1 - pct_usdc}, dias=90
            )

        resultado = otimizar_alocacao(
            saldo_brl=saldo_brl,
            saldo_usdt=saldo_usdt,
            saldo_usd=saldo_usd,
            previsao_gasto_brl_30d=gasto_30d,
            previsao_recebimento_usd_30d=recebimento_30d,
            previsao_pagamento_usd_30d=pagamento_30d,
            faixa_risco_stablecoin=faixa_risco,
            teto_stablecoin=teto_risco,
            es_stablecoin=es_atual,
        )

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Saldo Total (eq. BRL)", f"R$ {resultado['saldo_total_equivalent_brl']:,.0f}")
        col_m2.metric("Meses de Reserva", f"{resultado['meses_reserva_brl']}")
        col_m3.metric("Converter → BRL (gap reserva)", f"R$ {resultado['converter_usdt_para_brl']:,.0f}")
        col_m4.metric(
            "Exposição Cambial Líquida (30d)", f"US$ {resultado['exposicao_liquida_usd_30d']:,.0f}",
            help="Recebimento − pagamento em USD. Negativo = SHORT dólar (paga mais do que "
                 "recebe) — a decisão de hedge usa este número, não só 'tem recebimento em USD?' "
                 "(achado #6, corrige recomendação invertida pra perfil com passivo em USD).",
        )

        st.success(resultado["recomendacao_liquidez"])
        st.info(resultado["recomendacao_cambio"])
        st.info(resultado["sugestao"])
        st.caption(
            "Reserva de emergência em **cash** (BRL) — stablecoin NÃO é caixa equivalente "
            "(US GAAP/IFRS, ASU 2023-08) e entra só como capital de giro no trilho, com teto de "
            "política (5%), teto de depeg e haircut pelo ES (ADR-0009). Âncora de escala: "
            "Azul S.A. FY2024 (aérea com passivo em USD — caso clássico de tesouraria cambial)."
        )

        # --- FLUXO: o dinheiro que o projeto de fato movimenta (giro no trilho) ---
        # Distinto do ESTOQUE parado (reserva) abaixo. Não são a mesma fonte de valor:
        # este dinheiro SAI da empresa de qualquer forma (paga fornecedor); o ganho aqui é
        # custo de TRANSAÇÃO menor (Rail Comparator), não custo de OPORTUNIDADE de ficar parado.
        giro_brl = resultado["alocacao_stablecoin_pct"] * resultado["saldo_total_equivalent_brl"]
        st.divider()
        st.subheader("🔄 Capital em Giro no Trilho — o dinheiro do fluxo")
        col_g1, col_g2 = st.columns(2)
        col_g1.metric("Capital em trânsito (stablecoin)", f"R$ {giro_brl:,.0f}",
                       help="Fração do caixa alocada ao giro cross-border (teto triplo: fluxo × política × risco).")
        col_g2.metric("Valor de liquidez pós-haircut", f"R$ {resultado['valor_liquidez_stablecoin_brl']:,.0f}",
                       help=f"Descontado pelo ES de depeg ({es_atual:.2%}).")
        st.info(
            f"Este dinheiro **precisa sair da empresa** para pagar fornecedor — não está parado. "
            f"O ganho aqui não é 'render mais': é **pagar menos taxa pra mover** (spread + IOF + gas), "
            f"medido na aba **Rail Comparator**. É fluxo, não estoque — soma-se ao custo de carrego "
            f"abaixo, **não substitui** ele."
        )

        # --- 3º pilar: custo de carrego da reserva PARADA (ADR-0010) — estoque, não fluxo ---
        st.divider()
        st.subheader("💸 Custo de Oportunidade da Reserva — o dinheiro que fica parado")
        st.caption(
            "Diferente do capital em giro acima: isto é o **saldo que NÃO precisa se mover** "
            "(reserva de emergência + excedente). Ele fica ocioso o ano inteiro — daí o custo "
            "de oportunidade ser medido em taxa de referência (CDI/T-bill), não em spread de trilho."
        )
        with st.spinner("Consultando CDI (BCB) e T-bill (US Treasury)..."):
            carrego = custo_oportunidade_reserva(
                reserva_brl=resultado["brl_target"],
                posicao_usd=resultado["manter_usd"],
                yield_atual_pct=yield_atual,
            )

        col_o1, col_o2, col_o3 = st.columns(3)
        col_o1.metric("CDI (BRL)", f"{carrego['cdi_pct']:.2f}% a.a.")
        col_o2.metric("T-bill (USD)", f"{carrego['tbill_pct']:.2f}% a.a.")
        col_o3.metric(
            "Deixado na mesa", f"R$ {carrego['gap_total_anual_brl']:,.0f}/ano",
            help=f"≈ R$ {carrego['gap_total_diario_brl']:,.0f}/dia",
        )

        st.warning(
            f"A reserva está correta (cash), mas **parada rendendo {yield_atual:.1f}%**. "
            f"Movendo cada perna para o cash-equivalent do seu próprio mercado (fundo DI/BRL, "
            f"money market/USD) — **sem mudar o perfil de risco de depeg nem o compliance** — "
            f"você captura até **R$ {carrego['gap_total_anual_brl']:,.0f}/ano**."
        )
        if carrego["alerta_carry_trade"]:
            st.info(
                f"⚠️ Achado #7: o diferencial CDI−T-bill aqui é **{carrego['diferencial_juros_cdi_tbill_pct']:.1f}pp** "
                "— por paridade DESCOBERTA de juros, isso aproxima a depreciação cambial ESPERADA do "
                "BRL, não é rendimento sem contrapartida. A perna BRL do 'deixado na mesa' é em parte "
                "prêmio de carry trade cambial: sem risco de DEPEG (correto), mas não sem risco "
                "cambial algum — não confundir 'cash-equivalent' com 'risco zero'."
            )
        st.caption(
            "Custo de carrego = valor parado × (taxa de referência − yield atual). "
            "CDI via BCB SGS 4389, T-bill via US Treasury (fiscaldata) — ambos ao vivo. "
            "Este é o 3º pilar (Capital Markets & Funding): o capital dorme na reserva "
            "(estoque), não no giro em stablecoin (fluxo) — ADR-0010, supersede o ADR-0007 §B. "
            "**Não é um trade-off** (escolher um ou outro): são duas fontes de valor "
            "independentes e aditivas — capturáveis ao mesmo tempo, sem competir pelo mesmo real."
        )

        st.caption(
            f"Depeg Risk Engine: ES(97%) atual = {es_atual:.2%} → faixa **{faixa_risco}** "
            f"→ teto de alocação em stablecoin = {teto_risco:.0%} (calibrado com ES real dos eventos "
            "USDC-SVB mar/2023 e UST mai/2022 — ver ADR-0003)"
        )
        from src.depeg_risk import ES_STRESSED_FLOOR_SVB
        if es_atual < ES_STRESSED_FLOOR_SVB:
            st.caption(
                f"⚠️ Achados #3/#4: ES histórico é procíclico — em regime calmo como agora "
                f"({es_atual:.2%}), o haircut de liquidez usado acima NÃO cai para esse valor. "
                f"Ele tem um **piso de ES estressado** ({ES_STRESSED_FLOOR_SVB:.2%}, medido no "
                "próprio evento USDC-SVB em granularidade horária) — protege contra o risco de "
                "cauda que só reaparece quando a próxima crise já começou."
            )
