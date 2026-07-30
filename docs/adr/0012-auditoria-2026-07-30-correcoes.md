# ADR-0012: Auditoria 2026-07-30 — correções de coerência econômica, matemática e de dados

**Data**: 2026-07-30
**Status**: Accepted (implementado item a item, TDD)
**Contexto**: revisão completa do projeto (código + ADRs + auditorias anteriores) a pedido do usuário, antes de uma conversa com o autor do artigo de referência (3 pilares de tesouraria corporativa) que motivou o ADR-0007/0010. Encontrou 10 achados novos, distintos dos já resolvidos pela auditoria 2026-07-14 (F1-F9) e pelo ADR-0011.

> **Princípio guia** (herdado do ADR-0011 §6): onde existe dado de mercado gratuito que substitua uma premissa por medição, substituir. Onde o problema é estrutural (paridade de juros, ES procíclico, spread de mercado que varia por ticket), expor o disclaimer — não fingir uma correção que não existe pra ser feita de graça.

---

## 1. CONTEXTO (O QUÊ?)

A auditoria de 2026-07-14 e o ADR-0011 já haviam corrigido os furos de negócio mais graves (F1/F2: custo do trilho stablecoin, PIX dominando incondicionalmente) e feito o upgrade de rigor pós-aula (granularidade horária, order book real, carteira ponderada). Uma segunda leitura completa (código + testes + ADRs) achou uma camada distinta de problemas, alguns dos quais **sobreviviam justamente porque as correções anteriores pararam um passo antes do fim**:

| # | Achado | Módulo | Severidade |
|---|--------|--------|-----------|
| 6 | Hedge cambial decidido só por `recebimento>0`, ignora passivo em USD | otimizador | 🔴 Crítico — recomendação podia inverter |
| 10 | Fallback de "sem dado" retorna teto conservador (30%) mas ES=0 → haircut nulo | depeg_risk | 🔴 Crítico — incoerência interna |
| 9 | Slippage do USDC medido no order book do USDT + 4 chamadas de rede redundantes | comparador | 🟠 Alto |
| 8 | Prêmio de on-ramp mistura FX (PTAX D-1) com liquidez (preço cripto tempo real) | comparador | 🟡 Médio |
| 1 | Spread do Wire hardcoded em 2,5% (varejo) — manchete de economia não testada por sensibilidade | comparador | 🔴 Crítico — toca a narrativa central |
| 2 | Faixas de risco calibradas em ES diário; motor migrou pra horário (ADR-0011) sem recalibrar | depeg_risk | 🟠 Alto |
| 3/4 | ES por simulação histórica é procíclico — haircut de liquidez colapsa a ~0 em regime calmo | depeg_risk/otimizador | 🟠 Alto |
| 7 | Custo de carrego soma CDI e T-bill sem ressalva de paridade de juros; default de yield inflava o headline | custo_carrego | 🟡 Médio |
| — | `lru_cache` sem TTL congela taxas pra sempre num processo Streamlit de longa duração | coletor_precos | 🟡 Médio |
| — | `resolucoes_aplicadas` sempre as mesmas 3, independente da transação | compliance | 🟢 Baixo |

---

## 2. DECISÃO E IMPLEMENTAÇÃO (POR QUÊ / COMO?)

### 2.1 Hedge por exposição líquida, não por sinal de recebimento (#6)

`otimizador.py`: `exportador = recebimento > 0` decidia manter ou zerar a posição em USD. Uma empresa com passivo pesado em USD (a própria Azul, âncora de referência do ADR-0011 §5) pode ter `recebimento=50k, pagamento=250k` — recebimento positivo, mas **líquida SHORT em 200k USD**. O código recomendava liquidar USD: o oposto do correto.

**Decisão**: decisão de hedge passa a usar `exposicao_liquida_usd_30d = recebimento - pagamento`. Mantém posição em USD sempre que a exposição líquida for **diferente de zero** (long ou short), só zera quando `recebimento == pagamento`. Campo `exposicao_liquida_usd_30d` exposto no retorno e na UI.

### 2.2 Fallback do ES coerente entre teto e haircut (#10)

`avaliar_risco_atual`/`avaliar_risco_carteira` retornavam `("medio", 0.30, es=0.0)` quando a API falhava. Teto conservador (30%), mas `1 - 0.0 = 1` → **haircut nulo**. "Sem dado pra concluir nada" custava, na prática, zero.

**Decisão**: `ES_FALLBACK_SEM_DADO = FAIXAS_RISCO[0][1]` (0,05 — fronteira inferior da própria faixa "medio", não um número novo). O fallback agora é internamente consistente: mesma faixa, mesmo ES mínimo que a classifica.

### 2.3 Slippage por moeda certa, 1 book por moeda (#9)

`slippage_execucao` sempre consultava `order_book_usdt_brl`, inclusive para o trilho USDC — que tem profundidade própria e menor no Brasil. Além disso, os 4 trilhos stablecoin (USDT/USDC × ERC-20/Polygon) chamavam a função 4x para o mesmo `valor_brl`, gerando rede redundante.

**Decisão**: `order_book_usdc_brl` (Binance `USDCBRL`, par real, confirmado ao vivo). `slippage_execucao(valor_brl, moeda)` despacha pro book certo. `comparar_custos` busca o book **1x por moeda** (não por trilho) e reaproveita pra slippage e pra defasagem (§2.4).

### 2.4 Defasagem PTAX×Binance exposta, não escondida (#8)

`premio_onramp` compara preço CoinGecko (tempo real) contra PTAX (BCB, D-1). Em dia de câmbio volátil, essa defasagem de fonte pode dominar o número — e não existe FX oficial intradiário gratuito pra eliminar isso de vez.

**Decisão**: expor `defasagem_ptax_binance_pct` por trilho (mid do mesmo order book já buscado pro slippage vs. PTAX) e `LIMIAR_DEFASAGEM_PTAX_PERCENT` (1%). Acima do limiar, a UI avisa que o prêmio pode estar contaminado por câmbio, não custo real de liquidez. **Disclaimer, não correção** — mesmo princípio do ADR-0011 §6.

### 2.5 Spread do Wire parametrizável + fronteira de indiferença (#1)

`SPREAD_WIRE_PERCENT = 2.5%` era constante fixa (spread de varejo/PME). A manchete de "~90% de economia" nunca foi testada por sensibilidade a esse número — só ao IOF (ADR-0011 §1).

**Decisão**: `comparar_custos(..., spread_wire_percent=SPREAD_WIRE_PERCENT)` — parâmetro configurável (default preserva comportamento anterior), input no dashboard. Nova função `spread_indiferenca_wire(valor, tipo_operacao)`: calcula algebricamente o spread de Wire em que a conclusão INVERTE.

**Achado que essa correção revelou** (não um bug, um dado novo): para `importacao_bens` (IOF isento), a fronteira de indiferença é **positiva e realista de negociar (~0,84% num teste isolado)** — a manchete pode inverter na prática. Para `remessa_internacional_terceiros` (IOF 3,5%), a fronteira é **profundamente negativa** — nenhum spread real de Wire alcança; a arbitragem é estrutural, não depende de negociação. Isso não estava documentado antes: a robustez da narrativa **depende do tipo de operação de forma mais forte do que o ADR-0011 §1 já havia reconhecido**.

### 2.6 ES horário medido de verdade na janela do SVB (#2)

O ADR-0011 §2 trocou o cálculo AO VIVO pra granularidade horária, mas nunca refez a calibração de `FAIXAS_RISCO` — que segue ancorada no ES **diário** do SVB (1,76%). Em vez de supor que a recalibração era necessária, o motor real foi rodado contra a mesma janela histórica (2022-12-19 → 2023-03-19, dado ao vivo DefiLlama 1h).

**Resultado medido**: ES(97%) horário do evento USDC-SVB ≈ **4,18%** (pinado em teste, `test_es_horario_real_da_janela_svb_ainda_classifica_baixo_mas_com_margem_estreita`). A classificação **não muda** — 4,18% < 5% ainda cai em "baixo". Mas a margem de segurança cai de **3,24pp** (diário: 1,76% vs. 5%) para **0,82pp** (horário: 4,18% vs. 5%) — quase 4× mais estreita. **Não há recalibração de corte** (mudar 5% sem nova âncora empírica seria o número mágico que o ADR-0011 §6 recusa) — há documentação da margem real, que era maior do que o projeto comunicava.

### 2.7 Piso de ES estressado no haircut de liquidez (#3/#4)

VaR/ES por simulação histórica é **procíclico**: dá risco mínimo bem antes da crise (regime calmo) e máximo só depois do evento já ter passado (enquanto a janela de 90d ainda contém os piores dias) — o próprio deep-dive documenta o sintoma ("ES travado em 1,763% por mais de um mês") sem nomear a causa. Em regime calmo, `es_stablecoin` medido fica perto de zero e o haircut de liquidez desaparece junto — a mesma cegueira de cauda que fez Basel III/FRTB exigir, além do ES corrente, um **stressed ES** calibrado num período de estresse histórico, como piso.

**Decisão**: `ES_STRESSED_FLOOR_SVB = 0.0418` (o valor medido em §2.6, não um número novo). `otimizador.otimizar_alocacao` aplica `es_haircut = max(es_stablecoin, ES_STRESSED_FLOOR_SVB)` **só no haircut de liquidez** — a classificação de risco/teto de alocação continua seguindo o regime corrente (ADR-0004, por design: o teto legitimamente pode subir em calmaria real). O piso nunca abranda uma crise real (quando `es_stablecoin > piso`, usa o medido).

### 2.8 Ressalva de paridade de juros no custo de carrego (#7)

`custo_oportunidade_reserva` soma o gap em BRL (vs. CDI) com o gap em USD (vs. T-bill) convertido a spot. A soma está matematicamente correta, mas o diferencial CDI−T-bill, por **paridade descoberta de juros**, aproxima a depreciação cambial **esperada** do BRL — não é dinheiro sem contrapartida. A UI dizia "você captura R$X/ano sem risco adicional", o que overclaimava a perna BRL.

**Decisão**: expor `diferencial_juros_cdi_tbill_pct` e `alerta_carry_trade` (acima de `LIMIAR_CARRY_TRADE_PERCENT = 5.0`pp). UI corrigida: "sem risco de depeg" (verdadeiro) em vez de "sem risco adicional" (falso). Default de `yield_atual` (0%) relabelado explicitamente como cenário pior-caso, não estimativa realista para tesouraria de grande porte.

### 2.9 TTL nos caches de taxa (menor)

`@lru_cache(maxsize=1)` em `taxa_cdi`/`taxa_tbill`/`ptax_venda` nunca expira sozinho — num processo Streamlit de longa duração (deploy real, ADR-0006), a primeira consulta ficava congelada pro resto da vida do processo.

**Decisão**: TTL via bucket de tempo (`_bucket_tempo()`, 1h) — idioma padrão do Python pra expirar `lru_cache` sem dependência nova.

### 2.10 `resolucoes_aplicadas` reflete o que disparou (menor)

Retornava sempre `["BCB 561", "BCB 520", "BCB 521"]`, independente da transação. Agora só entra a resolução que de fato gerou erro/aviso naquela avaliação.

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- A manchete de economia (~90%) agora tem uma fronteira de sensibilidade explícita e calculável, em vez de ser apresentada como constante.
- O motor de risco ganha um segundo mecanismo de defesa (piso estressado) contra a cegueira de cauda que o próprio ADR-0004 já citava como risco de VaR paramétrico — aplicado agora também ao histórico.
- Achados que antes exigiam leitura cuidadosa de código (defasagem FX, carry trade, margem de calibração) agora são dados explícitos na UI.

**Negativas / débitos que permanecem:**
- `spread_indiferenca_wire` assume que o spread negociável cross-border não depende do próprio valor da fatura (na prática, tickets maiores negociam melhor spread — não modelado).
- `ES_STRESSED_FLOOR_SVB` é ancorado em **1 evento** (mesmo problema de amostra pequena do ADR-0004 §2.5) — é o melhor dado disponível, não uma calibração robusta.
- `caso_uso="domestico"` continua com um único trilho elegível (PIX) — falta TED como segundo trilho doméstico para comparação real; não implementado nesta rodada por falta de dado de custo de TED com fonte (evitar novo número mágico).

---

## 4. IMPACTO & VALIDAÇÃO

94 testes passando (73 pré-existentes + 21 novos, todos TDD: RED confirmado antes de cada correção). Suite completa: `python -m pytest -q`.

**Risco de regressão**: `otimizar_alocacao` muda a semântica de `valor_liquidez_stablecoin_brl` (agora nunca é maior que `giro × (1 − 0,0418)`, mesmo em regime calmíssimo) — qualquer teste futuro que assuma haircut ~0 precisa considerar o piso.

---

## 5. LINKS RELACIONADOS

- `docs/adr/0004-parametros-depeg-risk-engine.md` (calibração original das faixas, ES 97%, janela 90d)
- `docs/adr/0008-modelo-custo-honesto-rail-comparator.md` (F1/F2, base do comparador que o #1 refina)
- `docs/adr/0009-conformidade-tesouraria-corporativa.md` (teto triplo e haircut que o #3/#4 estende)
- `docs/adr/0010-custo-de-carrego-da-reserva.md` (3º pilar que o #7 ressalva)
- `docs/adr/0011-rigor-upgrade-pos-aula.md` (granularidade horária que o #2 recalibra; princípio "expor, não fingir medição" herdado no §6)
- `tests/test_es_horario_real_da_janela_svb_ainda_classifica_baixo_mas_com_margem_estreita` (medição pinada em teste, base do #2 e #3/#4)
