# ADR-0010: Custo de carrego da reserva (3º pilar) — supersede parcial do ADR-0007

**Data**: 2026-07-14
**Status**: Accepted
**Supersede**: ADR-0007 §2.2 (ponto B — yield sobre alocação em stablecoin). O ponto C (slippage por volume) do ADR-0007 **permanece válido** e é implementado aqui.

---

## 1. CONTEXTO (O QUÊ?)

O ADR-0007 aceitou implementar "Opportunity Cost": mostrar quanto a **stablecoin parada** deixava de render (yield de Aave via DefiLlama), fechando o 3º pilar do artigo de referência (Capital Markets & Funding).

**O ADR-0009 invalidou essa premissa.** Sob o modelo corporativo:
- Stablecoin deixou de ser "alocação de reserva parada" e passou a ser **capital de giro em trânsito** (~4,4% do caixa, transitando em dias).
- Render yield sobre dinheiro que fica dias no trilho é **irrelevante** — não é ali que o capital dorme.

Onde o capital **de fato** dorme numa tesouraria corporativa: na **reserva de cash** (no perfil de referência, ~43% do caixa, parada o ano inteiro).

---

## 2. DECISÃO (POR QUÊ?)

Reenquadrar o 3º pilar como **custo de carrego (carry cost) da reserva**, não como yield de stablecoin.

### 2.1 Custo de carrego

```
custo_carrego_anual = valor_parado × (taxa_referência / 100)
```

- **Reserva em BRL** → taxa de referência **CDI** (BCB SGS série 4389).
- **Posição em USD** → taxa de referência **T-bill** (US Treasury, avg interest rate de Treasury Bills).

O usuário informa o rendimento atual do caixa (`yield_atual`, default **0%** = conta não remunerada). O custo de oportunidade é o **gap**:

```
gap_anual = valor_parado × (taxa_referência − yield_atual) / 100
```

### 2.2 Por que isso NÃO viola o ADR-0009

Fundo DI / money market / T-bill **são cash-equivalents** (diferente de stablecoin). Mover a reserva de conta não remunerada para money market **não muda o perfil de risco nem o compliance** — a reserva continua sendo cash. É captura de valor sem risco adicional.

### 2.3 Fontes de dado (validadas ao vivo em 2026-07-14, grátis, sem API key)

| Taxa | Fonte | Endpoint | Valor observado |
|------|-------|----------|-----------------|
| CDI (% a.a.) | BCB SGS 4389 (mesma API do PTAX) | `api.bcb.gov.br/dados/serie/bcdata.sgs.4389/dados/ultimos/1` | 14,15% |
| Selic meta (% a.a.) | BCB SGS 432 | `.../bcdata.sgs.432/...` | 14,25% |
| T-bill (% a.a.) | US Treasury `fiscaldata` (JSON oficial) | `api.fiscaldata.treasury.gov/.../avg_interest_rates` (filtro `Treasury Bills`) | 3,706% (jun/2026) |

Mesmo padrão de degradação do resto do projeto: falha de API → fallback constante documentado, com log.

### 2.4 Ponto C do ADR-0007 (mantido): slippage por volume

O ADR-0008 já modelou o **prêmio spot** de on-ramp. O ponto C acrescenta **escala por volume**: conversões grandes sofrem mais atrito. Implementado como acréscimo por faixa (aproximação documentada, mesmo padrão do débito #1/#11) — **não** é modelo de order book real.

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- 3º pilar (Capital Markets & Funding) fechado com a métrica **corporativamente correta**, coerente com o ADR-0009.
- Reusa a API BCB já integrada (PTAX) — custo marginal de integração quase zero.
- Narrativa forte pro CFO: "sua política de reserva está certa; o cash é que está ocioso — R$42M/ano capturáveis sem risco adicional".

**Negativas / débitos:**
- `yield_atual` default 0% assume conta não remunerada — premissa; tesourarias grandes já costumam remunerar parte do caixa.
- **Custo de float do trilho** (capital preso durante os dias de settlement) não é modelado: é pequeno e tende a se cancelar entre trilhos (Wire também é T+2/T+5). Registrado como débito, não implementado.
- Slippage por volume segue aproximação por faixa, não order book (herda o débito #11).

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê rejeitada |
|-------|----------------------|
| Implementar ADR-0007 ponto B literal (yield de Aave sobre stablecoin) | Premissa morta pós-ADR-0009: stablecoin é giro em trânsito, não reserva parada — yield ali é irrelevante |
| Sugerir mover a reserva pra stablecoin com yield (Aave) | Viola ADR-0009: stablecoin não é cash-equivalent, não pode compor reserva |
| Modelar custo de float do trilho | Pequeno e ~cancela entre trilhos (Wire também demora); complexidade sem ganho de sinal |

---

## 5. IMPACTO & VALIDAÇÃO

**Métrica de sucesso:** card de Custo de Oportunidade no dashboard com CDI/T-bill reais; testes de propriedade (gap ≥ 0, gap cresce com taxa, fallback quando API cai). Slippage por volume com teste de monotonicidade (custo % não decresce com volume).

**Risco de regressão:** nenhum sobre o Depeg Engine; toca `coletor_precos.py` (novos coletores), módulo novo `custo_carrego.py`, `comparador.py` (slippage) e `app.py` (card).

---

## 6. LINKS RELACIONADOS

- `docs/adr/0007-yield-opportunity-cost-e-slippage-heuristico.md` (superseded parcialmente: ponto B morto, ponto C mantido)
- `docs/adr/0009-conformidade-tesouraria-corporativa.md` (reserva cash-only — a premissa que redireciona o 3º pilar)
- `docs/adr/0008-modelo-custo-honesto-rail-comparator.md` (on-ramp spot, que o slippage por volume estende)
- `src/custo_carrego.py`, `src/coletor_precos.py`, `src/comparador.py`
