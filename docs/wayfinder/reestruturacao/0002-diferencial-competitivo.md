---
tipo: grilling
status: resolvido
criado: 2026-07-09
---

# Ticket 0002: Qual é o Diferencial Competitivo Real

## Bloqueio
Existem dezenas de "comparadores de trilho de pagamento" e dashboards de compliance
no mercado/portfolio de outros candidatos. O que precisa ficar claro é: **qual módulo
é o "não tem em nenhum outro portfolio"?**

Candidatos:
- Rail Comparator (comparador.py) — commodity, qualquer engenheiro júnior faz
- Compliance Filter (BCB 519/520/521/561) — nicho regulatório BR, defensável mas raso
  (regra determinística, sem interpretação jurídica real — débito técnico #4)
- Liquidity Optimizer — depende do Depeg Risk Engine pra ter substância quantitativa real
- **Depeg Risk Engine** (VaR/ES sobre DefiLlama, calibrado com eventos reais USDC-SVB/UST)
  — este é o único módulo com rigor quantitativo de verdade (estatística de cauda,
  backtesting, persistência de série temporal). É o que mais se parece com trabalho
  de Data Scientist real, não CRUD com regras de negócio.

## Resultado
**Depeg Risk Engine é o protagonista.** Rail Comparator, Compliance Filter e
Liquidity Optimizer deixam de ser módulos de peso igual e passam a ser
"consumidores" do Depeg Risk Engine — o Optimizer já depende dele (ADR-0003),
o dashboard deve refletir essa hierarquia (aba de risco em primeiro lugar,
não enterrada), e README/pitch devem abrir com VaR/ES + backtest, não com
"comparador de trilho de pagamento".
