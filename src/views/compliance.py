import streamlit as st

from src.compliance import validar_transacao
from src.ui import intro


def renderizar():
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
