# ADR-0003: Pivot do Liquidity Optimizer para Depeg Risk Engine + Infra Postgres

**Data**: 2026-07-04
**Status**: Accepted
**Contexto**: StableTreasury — reexecução para elevar o projeto a peça forte de portfolio

---

## 1. CONTEXTO (O QUÊ?)

O PAVC audit (`docs/audit/pavc_audit.md`) documentou 3 falhas nunca corrigidas (margem gas fee, spread fixo, IOF stablecoin sem tratamento de risco fiscal) e uma quarta falha não documentada anteriormente: o `Liquidity Optimizer` aloca caixa por heurística fixa (50/30/20) sem nenhuma base quantitativa — não é modelo, é chute com aparência de modelo.

Avaliação honesta de mercado (sabatina com o usuário): o projeto tem baixo TAM real como produto (nenhuma empresa brasileira faz liquidação B2B via stablecoin em escala hoje) e não deve ser vendido como sistema de produção. Valor real está em ser **sinal de portfolio** — interseção rara de rigor quantitativo + regulatório (BCB) + crypto.

**Restrições técnicas:**
- Custo zero mantido (regra do projeto)
- Sem autenticação/multi-tenant, sem execução real de transação, sem assessoria jurídica/fiscal real (escopo negativo confirmado)
- Usuário está em pós-graduação de Data Science (FIAP) — decisões de infra devem priorizar aprendizado real (SQL/cloud), não o caminho mais fácil

---

## 2. DECISÃO (POR QUÊ?)

- **Manter**: Rail Comparator + Compliance Filter (gancho regulatório BCB 561, timing real out/2026 — diferencial do projeto)
- **Substituir**: heurística 50/30/20 do Liquidity Optimizer por um **Depeg Risk Engine** real:
  - Matemática: VaR / Expected Shortfall sobre desvio histórico do peg (USDT/USDC vs. USD)
  - Dado real: attestations Circle/Tether (públicas), proof-of-reserve on-chain (DefiLlama/Chainlink, grátis), eventos históricos reais (UST mai/2022, USDC-SVB mar/2023) como cenário de stress/backtest
- **Infra**: Postgres gerenciado (Supabase/Neon free tier) em vez de SQLite — histórico de cotações persistido, migrations reais, deploy público (link direto pro recrutador, sem clone de repo)

**Razão Principal (ROI):**
> "Se não fizermos isso: o projeto continua com um módulo central (Optimizer) que qualquer avaliador técnico reconhece como número inventado — mina a credibilidade dos outros 2 módulos que são rigorosos. Se fizermos: o projeto passa a ter um modelo de risco real, backtestável contra crises reais, e infra que demonstra competência de dado (não só de código)."

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- Optimizer deixa de ser "número mágico" e vira modelo com matemática defensável (VaR/ES)
- Histórico real de cotações (Postgres) habilita backtest e gráfico de série temporal — hoje o projeto é 100% stateless
- Deploy público mostra sistema fim-a-fim, não só repositório local

**Negativas:**
- Escopo cresce: precisa de pipeline de ingestão histórica (attestations + on-chain), não só chamada pontual de API
- Setup Postgres (mesmo grátis) é mais fricção inicial que SQLite
- Modelo de risco real exige que o usuário entenda VaR/ES a fundo antes de codar (decisão explícita do usuário: modo ensino antes de execução)

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê foi rejeitada |
|-------|----------------------|
| Pivot total para DAO Treasury Analyzer (100% dado real on-chain) | Perde o gancho regulatório BCB 561/Brasil, que é o diferencial de timing do projeto |
| Manter heurística 50/30/20, só documentar como "simplificação" | Não resolve o problema de credibilidade técnica; débito já documentado no PAVC sem correção é pior que não ter documentado |
| SQLite em vez de Postgres | Não gera aprendizado real de SQL/cloud que o momento de pós-graduação do usuário pede |

---

## 5. IMPACTO & VALIDAÇÃO

**Métrica de sucesso:**
- Gate interno: débitos PAVC fechados + cobertura de testes mantida/ampliada + dashboard público rodando com dado histórico real
- Gate externo (decisivo): reação de avaliação por pessoa real do setor fintech/crypto antes de declarar "pronto"

**Timeline:** execução em módulos, cada um precedido por sessão de ensino (matemática, racional, negócio, storytelling) antes do código — ver [[feedback_teach_first_execution]] na memória do usuário.

**Risco de regressão:** Rail Comparator e Compliance Filter não são tocados nesta fase — mudança isolada no Optimizer + infra.

---

## 5b. NOTA DE VERIFICAÇÃO (fonte de dado histórico corrigida em 2026-07-04)

Durante o ensino do Módulo 2 (dados reais), duas suposições foram testadas ao vivo antes de virar código:

- **CoinGecko `market_chart` (free tier) limita histórico a 365 dias** — confirmado via docs oficiais (`Demo plan: 1 year`). Insuficiente pra cobrir cenários de stress reais (UST mai/2022, USDC-SVB mar/2023), que estão fora dessa janela a partir de hoje.
- **Fonte corrigida**: `https://coins.llama.fi/chart/coingecko:{id}?start={unix_ts}&span=N&period=1d` (API de preço geral da DefiLlama, distinta da API de supply `stablecoins.llama.fi` que só tem `chainBalances`, sem série de preço). Testado ao vivo em 2026-07-04: retorna preço diário real cobrindo mai/2022 e mar/2023, sem API key, sem paywall de histórico.

Essa correção evita construir o Depeg Risk Engine sobre uma fonte que não alcança os próprios eventos que o modelo precisa detectar.

---

## 6. LINKS RELACIONADOS

- `docs/audit/pavc_audit.md` (falhas que motivaram o pivot)
- `docs/adr/0001-fontes-de-dados.md`, `docs/adr/0002-arquitetura-streamlit-modulos.md`
- `AGENTS.md` (Linguagem Ubíqua — será estendida com termos: VaR, Expected Shortfall, depeg, proof-of-reserve)