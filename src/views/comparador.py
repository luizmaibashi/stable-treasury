import streamlit as st

from src.comparador import comparar_custos, gerar_faturas_sinteticas
from src.ui import intro


def renderizar():
    st.header("Cenário de comparação de trilhos")
    intro(
        "Como as premissas alteram o custo estimado de cada trilho?",
        'Este é um cenário técnico, não uma cotação, recomendação de rota ou simulação de execução. Um "trilho" é o caminho '
        'que o dinheiro percorre: <span class="term">PIX</span> (só dentro do Brasil), <span class="term">Wire</span> '
        '(transferência bancária internacional) ou <span class="term">USDT/USDC</span> (ativos digitais).',
        'altere o caso de uso, o tipo de operação e o spread de Wire para observar a sensibilidade. A tabela só ordena os '
        'custos calculados pelas premissas declaradas; não afirma qual trilho deve ser usado.',
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

        if st.button("Simular cenário", type="primary"):
            with st.spinner("Calculando o cenário com as fontes disponíveis..."):
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

                    st.success(f"Menor custo no cenário: **{melhor['trilho'][0]}** ({melhor['custo_percent'][0]:.2f}%)")
                    if economia > 0:
                        st.info(f"Diferença calculada: R$ {economia:,.2f} ({pct:.2f} pp) entre os extremos do cenário")
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
                        "(ADR-0008). O resultado depende das premissas de custo, da defasagem entre fontes e "
                        "da elegibilidade regulatória; não é cotação nem conclusão jurídica."
                    )

                    if caso_uso == "cross_border":
                        from src.comparador import spread_indiferenca_wire
                        spread_indif = spread_indiferenca_wire(valor, tipo_op)
                        if spread_indif < 0:
                            st.caption(
                                f"📐 Fronteira de indiferença: nenhum spread real de Wire (≥0%) "
                                f"alcança o trilho stablecoin com as premissas deste cenário "
                                f"(achado #1). Isso não substitui uma cotação negociada."
                            )
                        else:
                            relacao = "ACIMA" if spread_wire > spread_indif else "ABAIXO"
                            st.caption(
                                f"📐 Fronteira de indiferença: com **{spread_indif:.2f}%** de spread "
                                f"no Wire, os dois trilhos empatam. O slider está **{relacao}** desse "
                                f"ponto — {'neste cenário, o Wire fica acima do custo calculado para stablecoin' if relacao == 'ACIMA' else 'neste cenário, o Wire já fica abaixo'} "
                                f"(achado #1; não é recomendação)."
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
