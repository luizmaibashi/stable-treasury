---
tipo: grilling
status: resolvido
criado: 2026-07-09
---

# Ticket 0001: Objetivo Real do Projeto Agora

## Bloqueio
Projeto está em `02_PORTFOLIO` (showcase técnico, "Build to Learn" pela taxonomia raiz).
Mas pivotou 2x: Rail Comparator → +Compliance → +Liquidity Optimizer → +Depeg Risk Engine.
Cada pivot adicionou escopo sem remover o anterior. Resultado: projeto faz 4 coisas
(comparar trilhos, filtrar compliance BCB, otimizar alocação, medir risco de depeg).

Não está claro se o objetivo é:
(a) Portfolio pra processo seletivo (Pós-Tech FIAP / vagas AI Engineer) — precisa de
    narrativa clara e "uma coisa que brilha", não 4 módulos médios
(b) Estudo técnico aprofundado de 1 tema (ex: Depeg Risk Engine com VaR/ES é o mais
    tecnicamente denso — poderia ser o produto principal, resto vira contexto)
(c) Produto real/MVP que pode virar Build to Earn — nesse caso débitos técnicos
    (dados sintéticos, spread estimado) viram bloqueadores reais, não "escopo negativo aceitável"

## Resultado
**Híbrido: portfolio + produto real.** Narrativa precisa ser forte o suficiente pra
processo seletivo, mas o core (Depeg Risk Engine) deve ter rigor técnico bastante
sólido pra, no futuro, evoluir pra produto real sem precisar reescrever a base
estatística. Consequência prática: débitos técnicos que travam "produto real"
(dados sintéticos de fatura B2B, spread estimado) continuam como limitação
documentada por agora — não bloqueiam o portfolio, mas ficam marcados como
"resolver primeiro se este projeto virar Build to Earn".
