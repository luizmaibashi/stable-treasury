import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.comparador import comparar_custos, gerar_faturas_sinteticas
from src.compliance import validar_transacao
from src.otimizador import otimizar_alocacao
from src.custo_carrego import custo_oportunidade_reserva
from src.coletor_precos import preco_stablecoin, ptax_venda
from src.depeg_risk import avaliar_risco_atual
from src.db import get_engine
from src.repositorio import ler_serie_risco


@st.cache_resource
def _engine():
    # cache_resource: reusa 1 engine entre reruns do Streamlit (não reabre conexão a cada clique)
    return get_engine()


st.set_page_config(
    page_title="StableTreasury",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 StableTreasury")
st.markdown("Motor de decisão para tesourarias — compara trilhos, valida compliance, otimiza liquidez.")

tab_rails, tab_compliance, tab_liquidity, tab_risco, tab_config = st.tabs([
    "📊 Rail Comparator",
    "🔒 Compliance Filter",
    "💧 Liquidity Optimizer",
    "📈 Histórico de Risco",
    "⚙️ Config",
])

with tab_rails:
    st.header("Comparador de Trilhos")

    col1, col2 = st.columns([1, 2])
    with col1:
        valor = st.number_input("Valor da fatura (BRL)", min_value=100, max_value=10_000_000, value=50000, step=1000)
        caso_uso = st.radio(
            "Caso de uso",
            options=["cross_border", "domestico"],
            format_func=lambda x: {"cross_border": "Cross-border (converte BRL↔USD)", "domestico": "Doméstico (BRL→BRL)"}[x],
            help="PIX só serve pagamento doméstico; Wire/USDT/USDC só cross-border. A comparação só faz sentido entre trilhos do mesmo caso de uso (ADR-0008).",
        )
        tipo_op = st.selectbox(
            "Tipo de operação",
            options=[
                "remessa_internacional_terceiros",
                "remessa_mesma_titularidade",
                "investimento_exterior",
                "cartao_internacional",
                "entrada_recursos_exterior",
                "stablecoin",
            ],
            format_func=lambda x: x.replace("_", " ").title(),
        )
        efx = st.checkbox(
            "Operação de eFX (câmbio eletrônico)",
            value=False,
            help="Se marcado, aplica a BCB 561: stablecoin proibido como trilho de liquidação em eFX (vigência out/2026).",
        )

        if st.button("Comparar trilhos", type="primary"):
            with st.spinner("Consultando preços on-chain..."):
                try:
                    df = comparar_custos(valor, tipo_op, caso_uso=caso_uso, eletronico_cambio=efx)
                    st.session_state["df_custos"] = df

                    melhor = df[0]
                    pior = df[-1]
                    economia = float(pior["custo_total_brl"][0]) - float(melhor["custo_total_brl"][0])
                    pct = float(pior["custo_percent"][0]) - float(melhor["custo_percent"][0])

                    st.success(f"Melhor trilho: **{melhor['trilho'][0]}** ({melhor['custo_percent'][0]:.2f}%)")
                    if economia > 0:
                        st.info(f"Economia potencial: R$ {economia:,.2f} ({pct:.2f} pp) vs. pior trilho")

                    st.dataframe(
                        df,
                        column_config={
                            "trilho": "Trilho",
                            "moeda": "Moeda",
                            "spread_brl": st.column_config.NumberColumn("Spread (R$)", format="%.2f"),
                            "tarifa_brl": st.column_config.NumberColumn("Tarifa (R$)", format="%.2f"),
                            "iof_brl": st.column_config.NumberColumn("IOF (R$)", format="%.2f"),
                            "gas_brl": st.column_config.NumberColumn("Gas (R$)", format="%.2f"),
                            "custo_total_brl": st.column_config.NumberColumn("Custo Total (R$)", format="%.2f"),
                            "custo_percent": st.column_config.NumberColumn("Custo (%)", format="%.2f%%"),
                        },
                        hide_index=True,
                        width="stretch",
                    )
                    st.caption(
                        "Custo do trilho stablecoin = spread on-ramp (BRL→USDT, prêmio real de "
                        "mercado) + gas + spread off-ramp (USDT→USD, 0,3% fixo). Não é 'só gas' "
                        "(ADR-0008). A economia vs. Wire existe porque o stablecoin dribla o IOF de "
                        "eFX — arbitragem que a BCB 561 encerra em out/2026."
                    )
                except Exception as e:
                    st.error(f"Erro ao comparar: {e}")

    with col2:
        st.subheader("Perfis de fatura")
        st.markdown("Geração sintética para 4 perfis de tesouraria.")
        if st.button("Gerar perfis sintéticos"):
            with st.spinner("Calculando para 4 perfis..."):
                df_perfis = gerar_faturas_sinteticas()
                st.session_state["df_perfis"] = df_perfis
                st.dataframe(
                    df_perfis,
                    column_config={
                        "perfil": "Perfil",
                        "valor_brl": st.column_config.NumberColumn("Valor (R$)", format="%.0f"),
                        "melhor_trilho": "Melhor Trilho",
                        "custo_melhor_brl": st.column_config.NumberColumn("Melhor Custo (R$)", format="%.2f"),
                        "custo_melhor_pct": st.column_config.NumberColumn("Melhor (%)", format="%.2f%%"),
                        "pior_trilho": "Pior Trilho",
                        "custo_pior_brl": st.column_config.NumberColumn("Pior Custo (R$)", format="%.2f"),
                        "custo_pior_pct": st.column_config.NumberColumn("Pior (%)", format="%.2f%%"),
                    },
                    hide_index=True,
                    width="stretch",
                )

with tab_compliance:
    st.header("Validador de Compliance BCB")

    col_a, col_b = st.columns(2)
    with col_a:
        transacao = {
            "id": st.text_input("ID da transação", value="TXN-001"),
            "tipo": st.selectbox(
                "Tipo de transação",
                options=["eletronico_cambio", "remessa_internacional", "pagamento_domestico", "tesouraria_propria"],
                format_func=lambda x: x.replace("_", " ").title(),
            ),
            "moeda_saida": st.selectbox("Moeda de saída", options=["USD", "BRL", "USDT", "USDC", "EUR"]),
            "trilho": st.selectbox("Trilho", options=["wire", "PIX", "USDT", "USDC"]),
            "valor_brl": st.number_input("Valor (BRL)", min_value=100, max_value=10_000_000, value=50000),
            "kyc_completo": st.checkbox("KYC completo", value=True),
        }

    with col_b:
        if st.button("Validar transação", type="primary"):
            resultado = validar_transacao(transacao)

            if resultado["permitido"]:
                st.success("✅ Transação permitida")
            else:
                st.error("❌ Transação bloqueada")

            if resultado["erros"]:
                st.subheader("Erros")
                for e in resultado["erros"]:
                    st.error(e)

            if resultado["avisos"]:
                st.subheader("Avisos")
                for a in resultado["avisos"]:
                    st.warning(a)

            st.caption(f"Resoluções aplicadas: {', '.join(resultado['resolucoes_aplicadas'])}")

with tab_liquidity:
    st.header("Otimizador de Liquidez")

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
            help="Quanto sua reserva já rende hoje. 0% = conta não remunerada. Usado pra calcular o custo de carrego vs. CDI/T-bill (ADR-0010).",
        )

    if st.button("Otimizar alocação", type="primary"):
        with st.spinner("Avaliando risco de depeg (VaR/ES sobre histórico real USDC)..."):
            # SIMPLIFICAÇÃO: risco medido só sobre USDC e aplicado ao total em stablecoin.
            # USDT tem perfil de risco distinto (reserva/attestation diferente) — débito
            # técnico documentado no AGENTS.md; ideal seria risco ponderado por composição.
            faixa_risco, teto_risco, es_atual = avaliar_risco_atual("usd-coin", dias=90)

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

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Saldo Total (eq. BRL)", f"R$ {resultado['saldo_total_equivalent_brl']:,.0f}")
        col_m2.metric("Meses de Reserva", f"{resultado['meses_reserva_brl']}")
        col_m3.metric("Converter → BRL (gap reserva)", f"R$ {resultado['converter_usdt_para_brl']:,.0f}")

        st.success(resultado["recomendacao_liquidez"])
        st.info(resultado["recomendacao_cambio"])
        st.info(resultado["sugestao"])
        st.caption(
            "Reserva de emergência em **cash** (BRL) — stablecoin NÃO é caixa equivalente "
            "(US GAAP/IFRS, ASU 2023-08) e entra só como capital de giro no trilho, com teto de "
            "política (5%), teto de depeg e haircut pelo ES (ADR-0009). Âncora de escala: Nubank FY2025."
        )

        # --- 3º pilar: custo de carrego da reserva (ADR-0010) ---
        st.divider()
        st.subheader("💸 Custo de Oportunidade da Reserva")
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
            f"Movendo para fundo DI / money market — que **continua sendo cash-equivalent**, "
            f"sem mudar o perfil de risco nem o compliance — você captura "
            f"**R$ {carrego['gap_total_anual_brl']:,.0f}/ano** sem risco adicional."
        )
        st.caption(
            "Custo de carrego = valor parado × (taxa de referência − yield atual). "
            "CDI via BCB SGS 4389, T-bill via US Treasury (fiscaldata) — ambos ao vivo. "
            "Este é o 3º pilar (Capital Markets & Funding): o capital dorme na reserva, "
            "não no giro em stablecoin (ADR-0010, supersede o ADR-0007 §B)."
        )

        st.caption(
            f"Depeg Risk Engine: ES(97%) atual = {es_atual:.2%} → faixa **{faixa_risco}** "
            f"→ teto de alocação em stablecoin = {teto_risco:.0%} (calibrado com ES real dos eventos "
            "USDC-SVB mar/2023 e UST mai/2022 — ver ADR-0003)"
        )

with tab_risco:
    st.header("Histórico de Risco de Depeg (ES ao longo do tempo)")
    st.markdown(
        "Série reconstruída sobre preço histórico real (DefiLlama, desde 2022) e persistida no "
        "banco. Cada ponto é o Expected Shortfall calculado sobre a janela de 90 dias terminada "
        "naquela data — mostra o que o modelo **teria feito** em cada momento (ADR-0004)."
    )

    ativo = st.selectbox("Stablecoin", options=["usd-coin", "tether"],
                         format_func=lambda x: {"usd-coin": "USDC", "tether": "USDT"}[x])

    try:
        serie = ler_serie_risco(_engine(), ativo)
    except Exception as e:
        serie = []
        st.warning(f"Banco indisponível ({e}). Rode `docker compose up -d` e a ingestão histórica.")

    if not serie:
        st.info("Sem snapshots de risco para este ativo. Rode a ingestão + geração de snapshots.")
    else:
        import polars as pl
        df = pl.DataFrame({
            "data": [s["ts"] for s in serie],
            "ES (97%)": [s["es"] for s in serie],
            "VaR (97%)": [s["var"] for s in serie],
        })
        st.line_chart(df, x="data", y=["ES (97%)", "VaR (97%)"])

        pico = max(serie, key=lambda s: s["es"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Snapshots", len(serie))
        c2.metric("Pico de ES", f"{pico['es']:.2%}", help=f"em {pico['ts'].date()}")
        c3.metric("Faixa no pico", pico["faixa"])
        st.caption(
            f"Pico de risco em **{pico['ts'].date()}** (ES {pico['es']:.2%}) — para USDC, "
            "coincide com a janela do colapso do SVB (mar/2023), detectado pelo modelo sem ajuste manual."
        )
        from src.depeg_risk import tamanho_cauda
        n_cauda = tamanho_cauda(90, 0.97)
        st.caption(
            f"⚠️ Robustez: com janela de 90 dias e confiança 97%, o ES é a média de apenas "
            f"**{n_cauda} piores dias** (cauda rasa) — estimador sensível a outlier. Combinado com a "
            "granularidade diária (suaviza mínimo intra-dia), o ES de cauda pode ser subestimado (F4/débito #8)."
        )


with tab_config:
    st.header("Configuração / Dados ao Vivo")

    if st.button("Atualizar cotações"):
        with st.spinner("Consultando APIs..."):
            usdt = preco_stablecoin("usdt")
            ptax = ptax_venda()
            if usdt:
                st.session_state["usdt_brl"] = usdt
            else:
                st.warning("⚠️ CoinGecko falhou. Usando preço estimado para USDT.")
            
            if ptax:
                st.session_state["ptax"] = ptax
            else:
                st.warning("⚠️ BCB SGS falhou. Usando valor PTAX estimado.")

            st.success("Cotações atualizadas (com fallbacks se necessário)!")

    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("USDT/BRL", f"R$ {st.session_state.get('usdt_brl', '—'):.2f}" if "usdt_brl" in st.session_state else "R$ —")
    col_c2.metric("PTAX venda", f"R$ {st.session_state.get('ptax', '—'):.4f}" if "ptax" in st.session_state else "R$ —")
    col_c3.metric("Spread estimado", "1.2–2.5%" if "usdt_brl" in st.session_state else "—")

    st.caption(
        "Preço via CoinGecko, câmbio via BCB SGS. Gas fee via Etherscan/PolygonScan **quando há API "
        "key configurada** — sem key, o gas cai para uma faixa fixa estimada (não on-chain ao vivo). "
        "Cotações podem ter até 5 min de latência (F6/ADR-0009)."
    )
