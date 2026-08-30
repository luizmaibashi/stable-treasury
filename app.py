import os
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Em produção (Streamlit Cloud) a DATABASE_URL vem dos secrets. Espelhamos pro os.environ
# para o db.py — que lê via os.environ — funcionar sem nenhuma mudança de código (ADR-0006).
try:
    if not os.environ.get("DATABASE_URL") and "DATABASE_URL" in st.secrets:
        os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]
except Exception:
    pass  # sem secrets.toml local (dev) — usa o Postgres do docker-compose

from src.comparador import comparar_custos, gerar_faturas_sinteticas
from src.compliance import validar_transacao
from src.otimizador import otimizar_alocacao
from src.custo_carrego import custo_oportunidade_reserva
from src.coletor_precos import preco_stablecoin, ptax_venda
from src.depeg_risk import avaliar_risco_carteira
from src.decisao_pre_pagamento import avaliar_decisao_pre_pagamento
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

# A primeira aba agora acompanha a decisão real do usuário: evidência antes da execução.
tab_decisao, tab_risco, tab_liquidity, tab_rails, tab_compliance, tab_config = st.tabs([
    "🗂️ Decisão pré-pagamento",
    "📈 Risco de Depeg",
    "💧 Liquidity Optimizer",
    "📊 Rail Comparator",
    "🔒 Compliance Filter",
    "⚙️ Config",
])

with tab_decisao:
    st.header("Dossiê de decisão pré-pagamento")
    intro(
        "Transforme duas cotações em uma decisão que outra pessoa consegue revisar.",
        "Registre a fatura e as condições recebidas de parceiros autorizados. O dossiê compara custo, prazo, "
        "caixa e exposição cambial usando apenas esses dados — sem buscar cotação de mercado ou mover dinheiro.",
        "preencha a fatura e duas cotações. O resultado não aprova a operação: ele mostra o que está pronto "
        "para aprovação humana e o que ainda precisa ser revisado.",
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
        spread_wire = st.slider(
            "Spread negociado no Wire (%)", min_value=0.0, max_value=3.0, value=2.5, step=0.1,
            help="2,5% é spread de varejo/PME. Tesouraria corporativa em ticket grande negocia "
                 "0,2–0,8%. A economia do stablecoin depende deste número tanto quanto do IOF "
                 "(achado #1) — mexa no slider e veja a conclusão mudar.",
        )

        if st.button("Comparar trilhos", type="primary"):
            with st.spinner("Consultando preços on-chain..."):
                try:
                    df = comparar_custos(
                        valor, tipo_op, caso_uso=caso_uso, eletronico_cambio=efx,
                        spread_wire_percent=spread_wire,
                    )
                    st.session_state["df_custos"] = df

                    melhor = df[0]
                    pior = df[-1]
                    economia = float(pior["custo_total_brl"][0]) - float(melhor["custo_total_brl"][0])
                    pct = float(pior["custo_percent"][0]) - float(melhor["custo_percent"][0])

                    st.success(f"Melhor trilho: **{melhor['trilho'][0]}** ({melhor['custo_percent'][0]:.2f}%)")
                    if economia > 0:
                        st.info(f"Economia potencial: R$ {economia:,.2f} ({pct:.2f} pp) vs. pior trilho")
                    elif caso_uso == "domestico":
                        st.caption(
                            "Doméstico só tem PIX elegível hoje — sem TED como segundo trilho pra "
                            "comparar (débito técnico conhecido, ver AGENTS.md). Esta aba não compara "
                            "nada neste caso de uso; use Cross-border pra ver a comparação real."
                        )

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
                            "defasagem_ptax_binance_pct": st.column_config.NumberColumn(
                                "Defasagem PTAX×Binance (%)", format="%.2f%%",
                                help="Divergência entre a PTAX (BCB, D-1) e o preço ao vivo na Binance. "
                                     "Acima do limiar, o prêmio de on-ramp pode refletir câmbio se "
                                     "movendo no dia, não o custo real do trilho (achado #8).",
                            ),
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

                    if caso_uso == "cross_border":
                        from src.comparador import spread_indiferenca_wire
                        spread_indif = spread_indiferenca_wire(valor, tipo_op)
                        if spread_indif < 0:
                            st.caption(
                                f"📐 Fronteira de indiferença: nenhum spread real de Wire (≥0%) "
                                f"alcança o trilho stablecoin aqui — a arbitragem é estrutural "
                                f"(IOF sozinho já garante a vantagem, achado #1)."
                            )
                        else:
                            relacao = "ACIMA" if spread_wire > spread_indif else "ABAIXO"
                            st.caption(
                                f"📐 Fronteira de indiferença: com **{spread_indif:.2f}%** de spread "
                                f"no Wire, os dois trilhos empatam. O slider está **{relacao}** desse "
                                f"ponto — {'a conclusão atual é robusta neste tipo de operação' if relacao == 'ACIMA' else 'nesta faixa, o Wire já é mais barato — a manchete de economia não se sustenta aqui'} "
                                f"(achado #1)."
                            )

                    from src.comparador import LIMIAR_DEFASAGEM_PTAX_PERCENT
                    defasagens = [
                        abs(d) for d in df["defasagem_ptax_binance_pct"].to_list() if d is not None
                    ]
                    if defasagens and max(defasagens) > LIMIAR_DEFASAGEM_PTAX_PERCENT:
                        st.warning(
                            f"⚠️ Defasagem PTAX×Binance de até {max(defasagens):.2f}% detectada. "
                            "O prêmio de on-ramp compara preço cripto em tempo real com a PTAX de D-1 "
                            "(BCB) — em dia de câmbio volátil, essa defasagem de fonte pode dominar o "
                            "número, não o custo real de liquidez do trilho (achado #8; não há FX "
                            "oficial intradiário gratuito para eliminar isso por completo)."
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

            if resultado["resolucoes_aplicadas"]:
                st.caption(f"Resoluções disparadas: {', '.join(resultado['resolucoes_aplicadas'])}")
            else:
                st.caption("Nenhuma resolução disparou para esta transação (BCB 561/520/521 avaliadas).")

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
