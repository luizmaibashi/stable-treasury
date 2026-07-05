# ADR-0002: Arquitetura Streamlit + Módulos Python

**Data**: 2026-07-04
**Status**: Proposed
**Contexto**: StableTreasury

---

## 1. CONTEXTO (O QUÊ?)

Precisamos de uma interface que demonstre 3 módulos de decisão:
- **Rail Comparator**: compara custo total entre Wire / PIX / USDT / USDC
- **Compliance Filter**: valida transação contra BCB 519-521-561
- **Liquidity Optimizer**: sugere alocação ótima entre BRL/USDT/USD

**Restrições técnicas:**
- Portfolio showcase: sem deploy em produção, sem autenticação
- Sem dependência do Shadow FX Terminal (independente)
- Custo operacional zero (Streamlit Community Cloud é grátis)
- Código legível e modular (recrutadores vão ler)

**Métricas:**
- Dashboard carrega < 3s
- Simulação de fatura retorna em < 1s
- Cobertura de testes > 70%

---

## 2. DECISÃO (POR QUÊ?)

**O que escolhemos:**
- **Streamlit** (app.py): dashboard único com tabs (Rail, Compliance, Liquidity, Config)
- **src/comparador.py**: Rail Comparator — função pura `comparar_custos(fatura: dict) -> DataFrame`
- **src/compliance.py**: Compliance Filter — `validar_transacao(transacao: dict) -> dict` com regras BCB
- **src/otimizador.py**: Liquidity Optimizer — `otimizar_alocacao(saldos: dict) -> dict`
- **src/iof_tabela.py**: singleton com `carregar_iof() -> dict` do YAML
- **src/coletor_precos.py**: wrappers CoinGecko + Etherscan + BCB

**ROI:**
> "Streamlit reduz custo de UI ~80% vs. React+FastAPI (sem deploy, sem API, sem frontend separado). Para portfolio showcase, a velocidade de entrega vale mais que a flexibilidade de um SPA."

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- Uma `pip install streamlit` e tudo funciona
- Deploy 1-click no Community Cloud
- Código modular testável independentemente
- Fácil de estender (só adicionar tab + função pura)

**Negativas:**
- Streamlit não escala para multi-usuário (mas não é necessário)
- UI limitada (não dá para fazer UX tipo SaaS)
- Estado global problemático (cache @st.cache_data mitigado)

**Timeline:**
- Implementação: 3-4 horas
- Benefit realization: imediata

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| FastAPI + React | Melhor UX, escalável | ❌ Overengineering para portfolio (2 semanas vs. 4 horas) |
| Jupyter Notebook | Análise interativa | ❌ Não é dashboard apresentável |
| Gradio | Interface rápida | ❌ Menos flexível que Streamlit para tabs |

---

## 5. IMPACTO & VALIDAÇÃO

**Métrica de sucesso:**
- `app.py` roda sem erros com `streamlit run app.py`
- Todos os módulos importáveis: `from src import comparador, compliance, otimizador`

**Testes:**
- `pytest tests/` com cobertura > 70%

---

## 6. REFERÊNCIAS

- [Streamlit Docs](https://docs.streamlit.io)
- PROBLEM.md
- AGENTS.md
