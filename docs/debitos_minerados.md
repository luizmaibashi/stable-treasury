# Débitos minerados — stable-treasury

> Rodada 1: 2026-08-22, via skill `/minerar-debitos`. Fonte: `AGENTS.md` § Débitos técnicos conhecidos (26 itens numerados). 5 marcados RESOLVIDO sem débito remanescente foram excluídos da mineração (#6, #8, #13, #22 — sem texto restante pra classificar).

| # | Débito (resumo) | Classificação | Destino |
|---|---|---|---|
| 1 | Spread bancário estimado por faixa pública, não cotação ao vivo | Específico | — decisão consciente de escopo, sem sinal generalizável |
| 2 | Faturas B2B sintéticas (mock) | Específico | — dado de demo, não é falha |
| 3 | Sem API REST (só dashboard + módulos Python) | Específico | — escopo de produto único |
| 4 | BCB 561 implementada sem interpretação jurídica | Específico | — domínio regulatório específico deste projeto |
| 5 | Liquidity Optimizer heurística fixa | RESOLVIDO | — sem débito remanescente |
| 7 | Depeg Risk Engine media só USDC | RESOLVIDO | — sem débito remanescente |
| 9 | `var_es_historico` clampa `confianca` fora de `[0,1]` sem validar/logar | Estrutural (gate novo) | **Corrigido em revisão (2026-08-22)**: classificação original ("já coberto por `silent-failure-hunter`") errava a Lei da Travessia contra si mesma — esse agente só roda sob invocação explícita de PR review, não é gate automático. Virou checklist manual novo em `AGENTS.md` § Regras de engenharia ("Software — guarda silenciosa") |
| 10 | `_utc_naive`/`_com_utc` assume UTC implícito sem validar | Estrutural (gate novo) | Mesmo gate novo do #9 — padrão repetido 2× no mesmo projeto |
| 11 | Heurística de slippage sem order book real | Específico | — aproximação de domínio documentada |
| 12 | Custo trilho stablecoin ignorava on/off-ramp | RESOLVIDO | — sem débito remanescente |
| 14 | Off-ramp stablecoin (0,3%) constante estimada, não medida | Específico | — mesmo padrão do #1 |
| 15 | `DIAS_SETTLEMENT`/`CAP_POLITICA_STABLECOIN` premissas de política | Específico | — configurável, documentado |
| 16 | ES robustez rasa (cauda ~3-65 amostras, autocorrelação) | Específico | — limitação estatística de domínio, parcialmente mitigada |
| 17 | Perfil de referência mistura dado real e premissa ilustrativa | Específico | — rotulado, documentado |
| 18 | `yield_atual` default 0% | Específico | — relabelado como pior caso explícito |
| 19 | Custo de float do trilho não modelado | Específico | — decisão consciente (ADR-0010) |
| 20 | Slippage por volume não modela order book real | Específico | — duplica #11 |
| 21 | Spread negociável não depende do valor da fatura (débito remanescente pós-ADR-0012) | Específico | — não modelado, decisão consciente |
| 23 | `ES_STRESSED_FLOOR_SVB` calibrado em n=1 evento histórico | **Corrigido (2026-08-22): Específico** | Classificação original ("instância do gate n+IC") era encaixe forçado — esse gate exige que n seja **citado** ao reportar o número, e o próprio débito #23 já cita n=1 explicitamente. Pelo critério do gate, isso passa; não é achado que ele pegaria. Já é disclosure correto, não geração de gate |
| 24 | TED não implementado (falta dado público de custo) | Específico | — decisão consciente, UI avisa |
| 25 | Prêmio on-ramp compara CoinGecko (tempo real) com PTAX (D-1) | **Corrigido (2026-08-22): Específico** | Classificação original ("instância do gate comparação-mesma-população/grão") também era encaixe forçado — aquele gate nasceu de comparação modelo-vs-baseline em ML (ADR-0005), contexto diferente de mistura de fontes de dado com cadência distinta numa fórmula de precificação. Projeto já mitiga com disclaimer (ADR-0012 #8) — sem relação direta com o gate citado |
| 26 | Custo de carrego conflates CDI/T-bill gap com carry trade | Específico | — mitigado com disclaimer (ADR-0012 #7), característica de mercado |

## Achado da rodada

**2 débitos (#9, #10) geraram gate novo, após autocorreção.** Classificação original ("já coberto por `silent-failure-hunter`") foi revisada: esse agente só roda sob invocação explícita de review de PR, não é sinal automático — chamar isso de "coberto" repetia a própria Lei da Travessia que a skill existe pra caçar (capacidade existir ≠ ela atravessar pra proteção que dispara sozinha). Virou 1 checklist manual novo em `AGENTS.md` § Regras de engenharia: "Software — guarda silenciosa" (parâmetro sem contrato de validade, clampado/assumido sem log). Padrão repetido 2× no mesmo projeto — se confirmou de novo na rodada do payflow, em forma diferente.

**2 débitos (#23, #25) reclassificados de "cobertura confirmada" pra "específico", 2ª rodada de revisão (2026-08-22).** Diagnóstico honesto: forcei os dois pra encaixar em gates existentes (n+IC, comparação-mesma-população) por semelhança de superfície, sem checar se o mecanismo do gate realmente se aplicava. #23 já cita `n` no próprio texto — passa o critério do gate, não é achado que ele pegaria. #25 é mistura de fonte de dado com cadência diferente numa fórmula de precificação, contexto distinto do gate de comparação modelo-vs-baseline em ML que ele foi comparado a. Lição pra próximas rodadas: "parece com o gate X" não é a mesma coisa que "é instância do gate X" — checar o mecanismo, não só o vocabulário.

**Resultado final inalterado: 0 gate novo de "cobertura confirmada", só os 2 de #9/#10.**
