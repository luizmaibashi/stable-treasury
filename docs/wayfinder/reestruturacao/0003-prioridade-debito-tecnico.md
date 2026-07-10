---
tipo: grilling
status: resolvido
criado: 2026-07-09
---

# Ticket 0003: Quais Débitos Técnicos Valem Corrigir Antes de "Vender" o Projeto

## Bloqueio
10 débitos técnicos documentados em AGENTS.md. Reestruturar sem filtrar prioridade
gera trabalho disperso. Preciso saber que nível de polimento o objetivo (ticket 0001)
exige.

Débitos que **parecem** mais críticos pra credibilidade técnica (rigor estatístico):
- #8: VaR/ES usa granularidade diária, subestima risco de cauda intra-dia real
  (ex: USDC tocou 0,8767 hourly em mar/2023, série diária só registra ~0,96) —
  isso é um viés conhecido e mensurável, corrigir ou pelo menos quantificar o gap
  fortalece MUITO a narrativa "eu sei os limites do meu próprio modelo"
- #9: `confianca` fora de [0,1] não valida, clampa silenciosamente — achado do PAVC
  audit, fix é barato (1 guard clause)
- #10: naive datetime assumido como UTC sem validar — mesma categoria (fix barato)

Débitos que são **escopo negativo aceitável** pra portfolio (não bloqueiam):
- #1, #2: spread estimado e faturas sintéticas — qualquer avaliador técnico entende
  que dado real de parceiro B2B não é acessível em projeto de portfolio
- #3: sem API REST — decisão de escopo consciente (ADR), não bug
- #7: teto único pro USDC/USDT — simplificação documentada, não erro

## Resultado
**Nenhum débito corrigido agora.** Prioridade é reestruturação de escopo/narrativa,
não polimento de código. Os 10 débitos continuam documentados em AGENTS.md como
estão. Reavaliar #8/#9/#10 numa sessão futura dedicada a hardening, depois que a
narrativa nova estiver assentada — não misturar as duas frentes.
