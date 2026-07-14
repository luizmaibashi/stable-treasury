# ADR-0007: Terceiro Pilar (Opportunity Cost/Yield) + Heurística de Slippage por Volume

**Data**: 2026-07-14
**Status**: **Partially Superseded** por [ADR-0010](0010-custo-de-carrego-da-reserva.md)
**Contexto**: Revisão externa (artigo sobre Cash Management/Hedging/Capital Markets, aplicado via análise LLM) comparando StableTreasury aos 3 pilares clássicos de tesouraria corporativa

> ⚠️ **Nota de supersessão (2026-07-14):** o **ponto B** deste ADR (yield/opportunity cost sobre a
> alocação em *stablecoin*) teve sua premissa invalidada pelo ADR-0009 — stablecoin deixou de ser
> "reserva parada" e virou capital de giro em trânsito, onde yield é irrelevante. O 3º pilar foi
> reenquadrado no **ADR-0010** como *custo de carrego da reserva de cash* (BRL vs CDI, USD vs T-bill).
> O **ponto C** (slippage por volume) permanece válido e é implementado pelo ADR-0010.
> O **ponto A** (hedge real) segue rejeitado, como decidido aqui.

---

## 1. CONTEXTO (O QUÊ?)

Estudo comparando o projeto a um artigo sobre tesouraria corporativa (3 pilares: Cash Management, Hedging/Risk, Capital Markets & Funding) trouxe 3 pontos de melhoria:

- **A**: Hedge real — sistema deveria não só medir risco (Depeg Engine) e reduzir exposição (Optimizer), mas executar hedge de verdade (comprar put option DeFi contra USDC)
- **B**: Pilar esquecido — se o Optimizer aloca 60% em stablecoin, esse valor rende 0% parado; falta visão de custo de oportunidade (yield de protocolos tipo Aave)
- **C**: Risco de liquidez do próprio rail — Rail Comparator escolhe via mais barata sem considerar se o volume da transação teria slippage significativo ao converter

Cada ponto foi avaliado contra o escopo negativo do ADR-0003 e as regras de engenharia do `AGENTS.md` antes de decidir.

---

## 2. DECISÃO (POR QUÊ?)

### A — REJEITADO (não implementar)

**Por quê X**: ADR-0003 fixou escopo negativo explícito — *"sem execução real de transação (nunca integra custodian/exchange real)"*. Comprar put option é execução de transação. Implementar de verdade exigiria integrar protocolo de opções DeFi (Lyra/Hegic), custodiar posição, gerenciar exercício — expande o projeto pra outro domínio, não é extensão natural do escopo atual.

**Por quê Y**: mesmo uma versão "fake" (só exibir texto "hedge sugerido: put X" sem executar) não agrega informação nova. O Liquidity Optimizer já comunica a decisão de risco reduzindo alocação — adicionar um rótulo de hedge sem lastro é decoração, não substância. Custo de implementar > valor entregue.

**Registro**: mantido como ponto de melhoria conhecido, não como débito técnico (não é uma lacuna do que foi prometido, é fronteira de escopo deliberada). Ver seção 4.

### B — ACEITO

Adicionar coletor de yield (DefiLlama `/yields`, mesma família de API já usada em `coletor_precos.py`, gratuita) e um card "Custo de Oportunidade" no dashboard: para o % alocado em stablecoin pelo Optimizer, mostrar quanto renderia num protocolo de referência (ex: Aave USDC) vs. parado.

**Razão**: fecha o 3º pilar (Capital Markets & Funding) que o artigo aponta como ausente, sem violar escopo negativo — é leitura de dado público, não execução. Mantém a regra "custo zero". Reaproveita padrão arquitetural existente (mesmo formato de coletor + fallback que `coletor_precos.py` já usa).

### C — ACEITO, como aproximação documentada

Adicionar heurística de spread adicional por faixa de volume em `comparador.py` (mesmo padrão do débito técnico #1, que já trata spread bancário como "estimado por faixa pública", não cotação ao vivo). Acima de determinado volume, aplicar acréscimo estimado simulando menor liquidez de conversão.

**Razão**: dado real de profundidade de order book (slippage real) não está disponível em API gratuita compatível com o restante do projeto. Resolver com heurística documentada é consistente com a forma como o projeto já trata outras limitações de dado (ver débito técnico #1). Não é modelagem real de slippage — é aproximação, documentada como tal para não passar falsa precisão.

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- Projeto passa a cobrir os 3 pilares clássicos de tesouraria corporativa (Cash Management, Risk, Funding), não só 2
- B usa mesma família de fonte de dado já validada (DefiLlama) — baixo risco de integração
- C fecha lacuna de realismo do Rail Comparator sem inventar modelo de slippage que o projeto não consegue validar

**Negativas:**
- Escopo do dashboard cresce (novo card/aba) — precisa avaliar se cabe nas 5 abas atuais ou se vira 6ª
- C é aproximação, não modelo real — precisa de disclaimer explícito na UI (mesmo padrão do spread bancário) para não ser lido como dado preciso
- B depende de disponibilidade/estabilidade do endpoint `/yields` da DefiLlama (não testado ainda ao vivo — repetir o processo de verificação que ADR-0003 fez para o endpoint de preço, seção 5b)

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê foi rejeitada |
|-------|----------------------|
| A — Hedge real (execução de put option) | Viola escopo negativo do ADR-0003; exige custódia/execução real, fora do domínio do projeto |
| A — Hedge "fake" (só rótulo sugestivo, sem lastro) | Sem valor informacional novo; risco de parecer feature real quando não é (falsa precisão) |
| C — Modelagem real de slippage (order book) | Sem fonte de dado gratuita compatível; complexidade não justificada pelo ganho de realismo |

---

## 5. IMPACTO & VALIDAÇÃO

**Métrica de sucesso:** card de Opportunity Cost funcionando com dado real da DefiLlama; heurística de volume em `comparador.py` com disclaimer visível na UI (mesmo padrão do spread bancário).

**Timeline:** independente do Deep Dive do Depeg Risk Engine (RETOMA_EM_CASA.md) — módulos distintos (`comparador.py` + novo coletor de yield vs. `depeg_risk.py`). Pode ser feito em qualquer ordem.

**Risco de regressão:** `depeg_risk.py` e `otimizador.py` não são tocados nesta fase — mudança isolada em `comparador.py` (heurística C) + novo módulo de yield (B) + `app.py` (novo card).

---

## 6. LINKS RELACIONADOS

- `docs/adr/0003-pivot-depeg-risk-engine.md` (escopo negativo que motivou rejeição do ponto A)
- `AGENTS.md` (débito técnico #1 — precedente de "estimado por faixa pública" reutilizado no ponto C)
- `src/comparador.py`, `src/coletor_precos.py` (módulos afetados)