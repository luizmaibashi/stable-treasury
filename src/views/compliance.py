import streamlit as st

from src.compliance import validar_transacao
from src.ui import intro


def renderizar():
    st.header("Cenário de regras BCB")
    intro(
        "Como regras codificadas alteram um cenário de transação?",
        'Este laboratório traduz regras selecionadas do Banco Central em condicionais determinísticas para fins de '
        'engenharia. Não é parecer jurídico, validação regulatória nem base para executar uma operação.',
        'preencha o cenário. <b>Vermelho</b> significa que a regra codificada o bloqueia; <b>amarelo</b> indica '
        'uma providência modelada. Confirme o enquadramento com instituição autorizada e assessoria competente.',
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
                st.success("✅ Cenário não bloqueado pelas regras codificadas")
            else:
                st.error("❌ Cenário bloqueado pelas regras codificadas")

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
