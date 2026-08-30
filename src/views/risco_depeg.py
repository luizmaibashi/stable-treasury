import streamlit as st

from src.repositorio import ler_serie_risco, ultima_data_preco
from src.ui import intro


def renderizar(engine):
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
        serie = ler_serie_risco(engine, ativo)
        ultimo_preco = ultima_data_preco(engine, ativo)
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
        if ultimo_preco is not None:
            st.caption(f"Último preço persistido: **{ultimo_preco.date().isoformat()} UTC**.")
        from src.depeg_risk import tamanho_cauda
        st.caption(
            "ℹ️ Granularidade (ADR-0011): o **risco atual** (aba Liquidez) usa série **horária** "
            f"— 90 dias = ~2160 pontos, cauda de **~{tamanho_cauda(2160, 0.97)} piores horas** e captura "
            "o mínimo intra-dia real (USDC tocou 0,8767 em mar/2023). Este **gráfico histórico** usa "
            "série diária (trend de anos, onde precisão de cauda importa menos)."
        )
