# ADR-0009: Conformidade do Liquidity Optimizer com finanças de tesouraria corporativa

**Data**: 2026-07-14
**Status**: Accepted
**Contexto**: revisão de conformidade financeira solicitada durante o Lote 3 da auditoria 2026-07-14. Objetivo: garantir que os números e a lógica de alocação reflitam como uma **empresa grande** de fato opera tesouraria, não uma heurística de runway de startup.

---

## 1. CONTEXTO (O QUÊ?)

O modelo do Liquidity Optimizer (mesmo após o F3) tinha dois pressupostos que **não passam em política de tesouraria corporativa**:

1. **Reserva dimensionada como "3 meses de despesa total"** — isso é heurística de runway de startup/PME, não política de empresa grande. Tesouraria corporativa dimensiona caixa mínimo por **DCOH (days cash on hand)**, cobertura de dívida de curto prazo e covenants, com **linha de crédito rotativa comprometida (RCF)** como backstop real de liquidez.

2. **Alvo de 50–60% do caixa em stablecoin** — insustentável. Tesouraria corporativa é **preservação de capital primeiro**. Nenhuma empresa grande aloca metade do caixa em stablecoin como reserva.

### O fato contábil decisivo

Sob **US GAAP e IFRS**, stablecoin **não é "caixa e equivalentes de caixa"**:
- Não é moeda de curso legal nem depósito à vista.
- Sob a **ASU 2023-08 (FASB)**, cripto é mensurada a valor justo como ativo — **fora** da linha de caixa.

**Implicação**: a reserva de emergência precisa ser **cash** (BRL + USD líquido). Stablecoin **não pode compor a reserva** — não é haircut maior, é **exclusão**.

---

## 2. DECISÃO (POR QUÊ?)

Reenquadrar o modelo na **estrutura de 3 tiers** da tesouraria corporativa:

```
Tier 1/2 — Reserva operacional (CASH ONLY): DCOH em BRL/USD líquido. Stablecoin excluída.
Tier 3   — Excedente: alocação com política de risco.
Backstop — RCF (fora do escopo do modelo, mencionada como premissa).
```

E tratar stablecoin como **capital de giro em trânsito no trilho de pagamento**, não investimento de reserva:

- **Reserva** = `DCOH_dias/30 × gasto_mensal`, satisfeita **só por cash** (BRL).
- **Stablecoin (working capital)** = valor em trânsito no trilho cross-border ≈ `fluxo_pagamento_cross_border × dias_settlement/30`.
- **Teto triplo** sobre a stablecoin: `min(necessidade_de_giro, cap_de_política, teto_de_depeg, 1 − fração_de_reserva)`.
  - `cap_de_política`: **5% do caixa** (topo do sleeve típico de ativos digitais, 1–5%, aprovado por board).
  - `teto_de_depeg`: o teto do Depeg Risk Engine (ES-based).
  - `1 − fração_de_reserva`: stablecoin nunca invade a reserva de cash.
- **ES como haircut de liquidez**: ao contar o valor de liquidez da stablecoin, aplica-se `valor × (1 − ES)` — reuso da métrica que o Depeg Engine já produz.

### Parâmetros de política (defaults, configuráveis)

| Parâmetro | Default | Racional |
|-----------|---------|----------|
| `DCOH_RESERVA_DIAS` | 60 | 2 meses de opex em cash — buffer operacional conservador de empresa grande (faixa típica 30–90) |
| `DIAS_SETTLEMENT` | 5 | janela de liquidação cross-border/off-ramp (T+2 a T+5) que dimensiona o in-transit |
| `CAP_POLITICA_STABLECOIN` | 0,05 | topo do sleeve de ativos digitais aprovável por política de board |

---

## 3. ÂNCORA EMPÍRICA — Nu Holdings (Nubank), FY2025

Ordem de grandeza calibrada num player real de fintech brasileira. **Fonte: Nu Holdings Form 20-F FY2025** (protocolado na SEC em 25/02/2026) e release 4T2025.

| Métrica (real, FY2025) | Valor |
|------------------------|-------|
| Receita total | US$ 15,8 bi (+37% a/a) |
| Lucro líquido | US$ 2,9 bi |
| Caixa & equivalentes (holding) | ~US$ 3,0 bi |
| Depósitos totais | US$ 41,9 bi |
| Carteira rende-juros | US$ 18,5 bi |
| Clientes | 131 mi (BR/MX/CO) |

**Ressalva de honestidade (importante):** Nubank é **banco** — balanço dominado por depósitos e carteira de crédito, não por caixa operacional pagando fornecedor no exterior. Usamos o Nubank **apenas como âncora de ordem de grandeza** (fintech BR de ~US$15,8bi receita → caixa operacional na casa das centenas de milhões de BRL). O perfil sintético do demo marca cada número como **(real, com fonte)** ou **(premissa ilustrativa)**. Não se afirma que o Nubank aloca em stablecoin.

---

## 4. CONSEQUÊNCIAS

**Positivas:**
- Modelo defensável numa mesa de tesouraria/compliance: reserva em cash, stablecoin como giro operacional com cap de política e haircut de risco.
- ES do Depeg Engine ganha um segundo uso legítimo (haircut de liquidez), não só teto de alocação.
- Resultado honesto: para tesouraria conservadora, stablecoin é **pequena** (dígito único %) — e o valor do projeto migra de "aloca cripto" para "roteia giro cross-border pelo trilho barato, com risco medido e regulatório embarcado".

**Negativas / débitos:**
- `DIAS_SETTLEMENT` e `CAP_POLITICA_STABLECOIN` são premissas de política, não medidas — configuráveis, documentadas como tal.
- RCF (backstop de liquidez real) fica fora do escopo do modelo — mencionada, não modelada.
- Perfil de referência mistura dado real de escala (Nubank) com premissa de fluxo cross-border (ilustrativa) — rotulado explicitamente.

---

## 5. ALTERNATIVAS DESCARTADAS

| Opção | Por quê rejeitada |
|-------|----------------------|
| Manter stablecoin 50–60% com disclaimer | Insustentável em política de tesouraria; contamina credibilidade do resto |
| Stablecoin como sleeve de investimento conservador (não giro) | Esvazia o propósito do projeto (trilho de pagamento); escolha do usuário foi "capital de giro" |
| Reserva "3 meses de despesa" | Heurística de runway de startup, não política de empresa grande |
| Incluir stablecoin na reserva com haircut | Viola classificação contábil (não é cash equivalent) — exclusão, não haircut |

---

## 6. IMPACTO & VALIDAÇÃO

**Métrica de sucesso:** testes de propriedade (a) reserva satisfeita só por cash; (b) stablecoin ≤ min dos 4 caps; (c) alocação soma 100%; (d) stablecoin excluída da reserva. Perfil de referência calibrado e rotulado.

**Risco de regressão:** muda a semântica de `alocacao_stablecoin_pct` (deixa de ser "50/60 capado por risco" e passa a ser "giro capado pelos 4 limites"). Testes antigos que cristalizavam os 50/60% precisam ser reescritos para o novo modelo.

---

## 7. LINKS RELACIONADOS

- `docs/audit/2026-07-14_auditoria_tecnica_negocio_matematica.md` (F3, origem)
- `docs/adr/0004-parametros-depeg-risk-engine.md` (ES que vira haircut/teto)
- `docs/adr/0003-pivot-depeg-risk-engine.md` (escopo negativo, preservação)
- Nu Holdings Form 20-F FY2025 — https://www.sec.gov/Archives/edgar/data/1691493/000129281426002166/nuform20f_2025.htm
- FASB ASU 2023-08 (mensuração de cripto a valor justo, fora de caixa & equivalentes)