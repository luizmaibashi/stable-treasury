---
projeto: stable-treasury
data: 2026-07-09
origem: wayfinder (5 tickets resolvidos)
---

# SPEC FINAL: Reestruturação StableTreasury

## Contexto
Projeto nasceu nebuloso (Rail Comparator → +Compliance → +Optimizer → +Depeg Risk
Engine), acumulando escopo a cada pivot sem reposicionar narrativa. Bridge de sessão
estava desatualizado (07-04, pré-pivot) — estado real já inclui Depeg Risk Engine
completo, testado, com PAVC audit rodado.

## Decisões (dos 5 tickets)

1. **Objetivo**: híbrido portfolio + produto real. Narrativa forte pra processo
   seletivo, mas rigor técnico suficiente pra evoluir a produto depois.
2. **Diferencial**: Depeg Risk Engine é protagonista. Comparator/Compliance/Optimizer
   viram módulos de apoio na narrativa (Optimizer já depende do Risk Engine de fato).
3. **Débito técnico**: nenhum fix agora. Reestruturação de narrativa não se mistura
   com hardening (#8/#9/#10 ficam pra sessão futura dedicada).
4. **Deploy**: sim, Streamlit Community Cloud gratuito. Quebra dev/prod parity do
   ADR-0005 conscientemente (SQLite em prod pública, Postgres continua em dev local)
   — precisa de ADR novo, não reescrita do 0005.
5. **Bridge**: estava obsoleto, já reconciliado (ticket 0005).

## Escopo de trabalho da reestruturação

### A. Narrativa (não-código)
- Reescrever abertura do README/pitch: liderar com Depeg Risk Engine (VaR/ES,
  calibração com eventos reais USDC-SVB/UST, backtest), não com "comparador de
  trilho de pagamento"
- Reordenar abas do dashboard (`app.py`): Depeg Risk Engine primeiro, demais módulos
  como "consumidores" do risco calculado

### B. Arquitetural (dispara ADR)
- Registrar ADR-0006: deploy público via Streamlit Community Cloud com SQLite,
  divergindo conscientemente do dev/prod parity do ADR-0005. Documentar trade-off
  custo-zero vs. paridade, e o que precisa mudar se/quando produto real exigir
  Postgres gerenciado.

### C. Execução (dispara spec-governance por tocar deploy)
- Configurar deploy Streamlit Community Cloud
- Validar app roda com SQLite em produção (sem dependência de Docker/Postgres local)
- Atualizar `AGENTS.md` (Mapa do projeto, ADRs registrados) refletindo protagonismo
  do Depeg Risk Engine e o ADR-0006 novo

### D. Fechamento
- `/session-bridge` novo refletindo reestruturação + deploy, substituindo bridge
  obsoleto de 07-04

## Próximo passo
Este spec está pronto pra `/grill-with-docs` (validação final de Linguagem Ubíqua +
ROI/riscos) antes de tocar em código, já que envolve decisão arquitetural (ADR-0006)
e mudança de escopo negativo implícito.
