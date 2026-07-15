import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.comparador import comparar_custos, gerar_faturas_sinteticas
from src.compliance import validar_transacao
from src.otimizador import otimizar_alocacao
from src.custo_carrego import custo_oportunidade_reserva
from src.coletor_precos import preco_stablecoin, ptax_venda
from src.depeg_risk import avaliar_risco_carteira
from src.db import get_engine
from src.repositorio import ler_serie_risco
from src.ui import aplicar_estilo, hero, intro


@st.cache_resource
def _engine():
    # cache_resource: reusa 1 engine entre reruns do Streamlit (não reabre conexão a cada clique)
    return get_engine()


st.set_page_config(
    page_title="StableTreasury",
    page_icon="🏦",
    layout="wide",
)

aplicar_estilo()
hero()

# Ordem de exibição alinhada à narrativa: o Depeg Risk Engine é o protagonista (lidera),
# seguido pela alocação que consome o risco, depois custo de trilho e legalidade.
tab_risco, tab_liquidity, tab_rails, tab_compliance, tab_config = st.tabs([
    "📈 Risco de Depeg",
    "💧 Liquidity Optimizer",
    "📊 Rail Comparator",
    "🔒 Compliance Filter",
    "⚙️ Config",
])

with tab_rails:
    st.header("Comparador de Trilhos")
    intro(
        "Qual via de pagamento custa menos para mandar dinheiro ao exterior?",
        'Um "trilho" é o caminho que o dinheiro percorre: <span class="term">PIX</span> (só dentro do Brasil), '
        '<span class="term">Wire</span> (transferência bancária internacional) ou <span class="term">USDT/USDC</span> '
        '(dólares digitais). Cada um tem um custo total diferente: spread de câmbio, imposto (IOF), tarifas e taxa de rede.',
        'a tabela ordena do <b>mais barato ao mais caro</b>. O trilho stablecoin costuma custar ~90% menos que o Wire — '
        'mas isso muda conforme o <b>tipo de operação</b>: importar bens é isento de IOF, então a vantagem encolhe.',
    )

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
                "importacao_bens",
                "importacao_servicos",
                "remessa_mesma_titularidade",
                "investimento_exterior",
                "cartao_internacional",
                "entrada_recursos_exterior",
                "stablecoin",
            ],
            format_func=lambda x: x.replace("_", " ").title(),
            help="A economia do stablecoin depende do IOF: máxima em remessa/serviços (3,5%), quase nula em importação de bens (isento — Decreto 6.306 Art. 15-B). ADR-0011.",
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
    intro(
        "Essa operação é permitida pela regulação brasileira?",
        'O Banco Central tem regras sobre usar ativos digitais em câmbio. A mais importante: a '
        '<span class="term">Resolução BCB 561</span> proíbe stablecoin como via de liquidação em câmbio '
        'eletrônico a partir de <b>out/2026</b> — é o prazo de validade da economia. Outras regras exigem '
        'KYC (identificação) e declaração de valores acima de R$ 500 mil.',
        'preencha a operação e valide. <b>Vermelho</b> = bloqueada (ilegal); <b>amarelo</b> = permitida, '
        'mas exige uma providência. Teste "Eletrônico Câmbio" + trilho USDT para ver a BCB 561 bloquear.',
    )

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
            help="Quanto sua reserva já rende hoje. 0% = conta não remunerada. Usado pra calcular o custo de carrego vs. CDI/T-bill (ADR-0010).",
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
            "política (5%), teto de depeg e haircut pelo ES (ADR-0009). Âncora de escala: "
            "Azul S.A. FY2024 (aérea com passivo em USD — caso clássico de tesouraria cambial)."
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
    st.header("Risco de Depeg ao longo do tempo")
    intro(
        "Quão perto a stablecoin já chegou de quebrar — e quando?",
        'O <b>Expected Shortfall (ES)</b> responde: "nos piores cenários, quanto a moeda perde da paridade?". '
        'É a mesma métrica de risco que os bancos usam (padrão Basel). O gráfico reconstrói esse risco a cada '
        'semana desde 2022, sobre o preço real da moeda.',
        'procure o <b>pico em março de 2023</b>: é o colapso do banco SVB, onde o USDC despencou para US$ 0,88. '
        'Ele aparece <b>sozinho</b> — ninguém programou essa data. O modelo descobre a crise porque o preço real '
        'caiu. É a prova de que o motor funciona.',
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
        # ES em âmbar (a métrica de risco que manda), VaR em cinza — paleta do painel
        st.line_chart(df, x="data", y=["ES (97%)", "VaR (97%)"], color=["#F2B03D", "#6B7A93"])

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
        st.caption(
            "ℹ️ Granularidade (ADR-0011): o **risco atual** (aba Liquidez) usa série **horária** "
            f"— 90 dias = ~2160 pontos, cauda de **~{tamanho_cauda(2160, 0.97)} piores horas** e captura "
            "o mínimo intra-dia real (USDC tocou 0,8767 em mar/2023). Este **gráfico histórico** usa "
            "série diária (trend de anos, onde precisão de cauda importa menos)."
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
