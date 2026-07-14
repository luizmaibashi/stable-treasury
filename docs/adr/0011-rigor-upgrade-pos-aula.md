# ADR-0011: Rigor upgrade pós-aula — premissas viram medições

**Data**: 2026-07-14
**Status**: Accepted (implementação incremental, item a item)
**Contexto**: revisão crítica do usuário sobre a `AULA_TECNICA_COMPLETA.md`. Seis questões, cinco viraram melhorias reais de rigor; uma (cap de política) permanece premissa por ser normativa, não de mercado.

> **Princípio guia**: onde existe dado de mercado gratuito que substitua uma premissa por uma medição, substituir. Onde a premissa é normativa (decisão de board), mantê-la explícita — fingir medição seria o "número mágico" que o ADR-0003 combateu.

---

## 1. IOF de importação isento — correção de viés da manchete

### Contexto
O `iof_aliquotas.yaml` não tinha a operação de **importação de bens**, e o demo defaultava para `remessa_internacional_terceiros` (3,5%) — o caso que **mais infla** a economia do stablecoin. Viés inconsciente, mesma família do F1/F2.

### Fato regulatório (Decreto 6.306/2007, Art. 15-B §1º)
| Operação de câmbio (PJ) | IOF |
|---|---|
| **Importação/exportação de bens** (comércio exterior) | **0% — isento** (Art. 15-B §1º, I e II) |
| Importação de **serviços** | 0,38% |
| Remessa a terceiros / serviços sem investimento | 3,5% |
| Investimento no exterior | 1,10% |
| Entrada de recursos | 0,38% |

Fontes: [Decreto 6.306 Art. 15-B (Jusbrasil)](https://www.jusbrasil.com.br/topicos/28087594/artigo-15b-do-decreto-n-6306-de-14-de-dezembro-de-2007), [Brasil Tax 2026](https://brasiltax.com/blog/iof-o-que-voce-precisa-saber-agora/), [Safra](https://oespecialista.safra.com.br/iof-no-cambio-remessas-exterior-2026/).

### Decisão
Adicionar `importacao_bens` (0%) e `importacao_servicos` (0,38%) ao YAML. **Não** trocar o 3,5% (correto para remessa/serviços a terceiros).

**A narrativa fica mais sofisticada, não mais fraca:** a arbitragem do stablecoin é **máxima onde o IOF é alto** (serviços/remessa a terceiros, 3,5%) e **quase nula onde a operação já é isenta** (importação de bens). O dashboard passa a deixar isso explícito — a economia depende do **tipo de operação**, não é um número universal.

---

## 2. Granularidade horária — conserta F4 (cauda rasa) + débito #8 (subestima cauda) juntos

### Decisão
Trocar `period=1d` por `period=1h` na DefiLlama para o cálculo de risco.

| | Diário | Horário |
|---|--------|---------|
| Amostras em 90 dias | 90 | ~2.160 |
| Cauda a 97% | **3** (ruidoso) | **~65** (robusto) |
| Mínimo USDC mar/2023 | ~0,96 (suavizado) | **0,8767** (real) |

**Por que é limpo (não precisa reescalar):** a métrica é **desvio do peg** (`preço − 1,00`), um *nível*, não um *retorno*. A regra do √t (escala de horizonte) **não se aplica** a níveis. Hora é estritamente mais informativo que dia, sem ajuste de escala. Se a métrica fosse retorno, misturar horizontes exigiria reescalar — não é o caso.

### Consequência
Ingestão 24× maior; janela do backtest passa a contar em horas. Débitos #8 e F4 fechados.

---

## 3. Order book real (Binance) — slippage e off-ramp viram medição de microestrutura

### Contexto
`SPREAD_OFFRAMP_PERCENT` (0,3%) e `FAIXAS_SLIPPAGE` eram premissas por faixa. A Binance expõe order book de USDT/BRL público e gratuito (`/api/v3/depth`).

### Decisão
Calcular o **preço de execução real (VWAP)** caminhando o order book nível a nível para o volume dado. Slippage = `(VWAP − mid) / mid`. Isso é o que uma mesa de fato faz: transforma "acréscimo por faixa" em **medição de profundidade de mercado**.

Fallback (API fora / volume acima da profundidade disponível): a heurística por faixa atual, documentada.

---

## 4. ES ponderado por carteira (USDT + USDC, com correlação) — corrige débito #7

### Contexto
O risco era medido só sobre USDC e aplicado ao total em stablecoin. USDT tem perfil de reserva/attestation distinto.

### Decisão (método correto)
**Não** é média dos ES individuais (ignora correlação). Constrói a **série de desvio da carteira**:
```
desvio_carteira(t) = w_usdc · desvio_usdc(t) + w_usdt · desvio_usdt(t)
ES = var_es_historico(desvio_carteira)
```
A correlação (e o benefício de diversificação) **emerge do dado**, não é imposta. Ambas as séries já vêm da DefiLlama.

---

## 5. Âncora de referência — trocar Nubank por perfil de passivo em USD

### Contexto
Nubank é **banco** — balanço de depósitos/carteira, âncora fraca para "tesouraria corporativa cross-border". Melhor analog: empresa com **passivo pesado em USD e receita em BRL** (o caso clássico de hedge cambial corporativo).

### Decisão
Trocar por **companhia aérea brasileira** (GOL/Azul) — leasing, combustível e manutenção em USD, receita em BRL, 20-F público. Exemplo de livro-texto de tesouraria FX. Custo: baixo (só `perfil_referencia.py` + nota). Números reais a puxar do 20-F mais recente.

---

## 6. O que NÃO vira medição — `CAP_POLITICA_STABLECOIN` (honestidade)

Cap de sleeve de ativo digital (5%) é **decisão normativa do board**, não quantidade de mercado. Não existe fórmula que descubra quanto uma empresa *deve* permitir — é apetite a risco. Máximo honesto: ancorar em survey de política de tesouraria (AFP) e manter configurável. **Fingir medição aqui seria o número mágico do ADR-0003.**

---

## 7. LINKS

- `docs/AULA_TECNICA_COMPLETA.md` (origem das questões)
- `docs/adr/0008` (custo do Rail Comparator, que o #1 e #3 refinam)
- `docs/adr/0004` (parâmetros do risco, que o #2 e #4 refinam)
- `docs/adr/0009` (perfil corporativo, que o #5 recalibra)