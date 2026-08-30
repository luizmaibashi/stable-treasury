import streamlit as st

from src.coletor_precos import preco_stablecoin, ptax_venda


def renderizar():
    st.header("Configuração / Fontes públicas")

    if st.button("Consultar fontes"):
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

            st.success("Fontes consultadas; fallbacks podem ter sido aplicados.")

    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("USDT/BRL", f"R$ {st.session_state.get('usdt_brl', '—'):.2f}" if "usdt_brl" in st.session_state else "R$ —")
    col_c2.metric("PTAX venda", f"R$ {st.session_state.get('ptax', '—'):.4f}" if "ptax" in st.session_state else "R$ —")
    col_c3.metric("Spread estimado", "1.2–2.5%" if "usdt_brl" in st.session_state else "—")

    st.caption(
        "Preço via CoinGecko, câmbio via BCB SGS. Gas fee via Etherscan/PolygonScan **quando há API "
        "key configurada** — sem key, o gas cai para uma faixa fixa estimada (não on-chain ao vivo). "
        "As observações têm cadência e latência próprias; não são cotações garantidas nem dados em tempo real."
    )
