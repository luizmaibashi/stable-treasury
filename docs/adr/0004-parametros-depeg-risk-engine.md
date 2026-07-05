# ADR-0004: Parâmetros e calibração do Depeg Risk Engine

**Data**: 2026-07-04
**Status**: Accepted
**Contexto**: StableTreasury — formaliza os números que governam a lógica de risco de `src/depeg_risk.py`

> Complementa o ADR-0003 (que decidiu *substituir a heurística por VaR/ES*).
> Este ADR documenta *com quais parâmetros* — a decisão de negócio mais sensível do projeto,
> já que esses números definem quanto capital corporativo fica exposto a risco de depeg.

---

## 1. CONTEXTO (O QUÊ?)

Depois de decidir usar VaR/Expected Shortfall (ADR-0003), restam 4 escolhas quantitativas
que não são óbvias e que, se ficarem só em comentário de código, tornam o modelo indefensável
numa avaliação técnica ("por que teto de 30%?"):

1. Método de VaR (histórico vs. paramétrico vs. Monte Carlo)
2. Métrica de perda (retorno dia-a-dia vs. desvio direto do peg)
3. Nível de confiança do VaR/ES
4. Janela histórica
5. Cortes das faixas de risco e tetos de alocação

---

## 2. DECISÃO (POR QUÊ?)

### 2.1 Método: VaR **histórico** (não paramétrico)
Peg de stablecoin **não é distribuição normal** — é quase-constante em ~1,00 com saltos raros e
gordos na cauda (ver eventos reais no ADR-0003). VaR paramétrico (assume normal) subestimaria
grosseiramente o risco de cauda, que é justamente o que importa. VaR histórico usa a distribuição
empírica real, incluindo os saltos.
> **Negócio**: modelo honesto por construção — não "esconde" o risco assumindo normalidade.

### 2.2 Métrica: **desvio do peg** (`preço − 1,00`), não retorno dia-a-dia
Uma queda gradual de $1,00 → $0,90 em vários passos pequenos tem retorno diário baixo em cada passo,
mas o desvio acumulado revela o depeg. Para stablecoin, o que interessa é distância da paridade,
não variação relativa entre dias. (Código: `src/depeg_risk.py::desvio_peg`.)

### 2.3 Confiança: **97%**
Basel III/FRTB padronizou **Expected Shortfall a 97,5%** como métrica regulatória de risco de mercado
pós-2008 (substituindo VaR 99%). Adotar ~97% alinha o modelo ao padrão que reguladores bancários
reais usam.
> **Negócio/storytelling**: "meço risco como um banco mede, não como um tutorial mede".

### 2.4 Janela: **90 dias**
Um trimestre. Casa com a cadência de attestation (trimestral, Tether) e preserva relevância do
**regime atual** — janela longa demais dilui o risco de hoje com calmaria antiga; curta demais é ruído.

### 2.5 Faixas de risco e tetos — calibradas com ES **real** dos 2 eventos históricos
| Faixa | Corte (ES) | Teto alocação stablecoin | Âncora empírica |
|-------|-----------|--------------------------|-----------------|
| baixo | ES < 5% | 60% | pior evento real recuperável (USDC-SVB, ES≈1,76%) fica aqui com folga |
| médio | 5% ≤ ES < 30% | 30% | buffer conservador — zona não observada em stablecoin fiat-backed |
| alto | ES ≥ 30% | 10% | cobre o caso catastrófico real (UST, ES≈99,3%) com margem enorme |

**Faixas discretas, não fórmula contínua** (decisão do usuário): alocação de capital precisa ser
auditável por comitê. "Está na faixa de risco médio" é defensável numa mesa de compliance;
"a fórmula deu 31,4%" não é. Espelha o rating de crédito bancário (AAA/BB/CCC).
(Código: `src/depeg_risk.py::FAIXAS_RISCO` e `classificar_risco_e_teto`.)

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- Todo número do motor de risco tem justificativa rastreável (regulatória ou empírica)
- Faixas ancoradas em ES real de crise, não em opinião

**Negativas / limitações (débitos técnicos, ver AGENTS.md #7 e #8):**
- Risco medido só sobre USDC e aplicado ao total em stablecoin (USDT tem perfil distinto)
- Granularidade diária subestima o mínimo intra-dia real (USDC tocou 0,8767 hourly em mar/2023)
- Cortes 5%/30% são calibração de engenharia com 2 pontos de âncora — mais eventos históricos
  refinariam as fronteiras

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê rejeitada |
|-------|----------------------|
| VaR paramétrico (normal) | Subestima cauda gorda; falso senso de segurança — o erro que quebrou bancos em 2008 |
| Confiança 99% | VaR 99% foi o padrão pré-2008; Basel migrou pra ES 97,5% justamente por cegueira de cauda |
| Fórmula contínua `teto = f(ES)` | Não auditável por comitê; número "exato" é indefensável sem faixa |
| Janela de 365 dias | Dilui regime atual com calmaria antiga; para risco corrente, trimestre é mais informativo |

---

## 5. IMPACTO & VALIDAÇÃO

**Métrica de sucesso:** cada parâmetro do motor responde a "por quê esse número?" com fonte
(Basel, cadência de attestation, ES real de evento). Testado em `tests/test_depeg_risk.py`
(classificação nas 3 faixas ancorada nos ES reais).

**Risco de regressão:** mudar qualquer corte/teto exige atualizar os testes de classificação —
os testes travam a calibração contra mudança acidental.

---

## 6. LINKS RELACIONADOS

- `docs/adr/0003-pivot-depeg-risk-engine.md` (decisão de usar VaR/ES)
- `docs/audit/pavc_audit.md` (débito da heurística que este motor substitui)
- `src/depeg_risk.py` (implementação), `tests/test_depeg_risk.py` (calibração travada)
- Basel III/FRTB — Expected Shortfall 97,5% como métrica regulatória de risco de mercado