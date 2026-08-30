# StableTreasury — A Jornada de Negócio Ponta a Ponta

> **ARQUIVO HISTÓRICO — não usar como narrativa pública.** Este cenário de negócio foi produzido antes de a pesquisa encerrar a hipótese comercial. Mantém valor como registro das premissas e dos limites que foram testados, mas não representa cliente, benefício, economia, recomendação ou produto validado. A demonstração pública atual é técnica e centrada no Depeg Risk Engine.

> **Player**: Azul S.A. (FY2024: R$19,5bi receita, R$7,5bi liquidez total, passivo pesado em USD)
> **Problema**: Todo mês precisa pagar ~US$250mi em leasing de aeronaves, combustível e manutenção no exterior.
> **Sistema**: StableTreasury — motor de decisão que compara trilhos, mede risco de stablecoin e otimiza alocação.

---

## 1. O Cenário — Terça-Feira, 08:00

A mesa de tesouraria da Azul abre o dashboard. Na tela:

```
Caixa disponível:
  BRL: R$ 4.000.000.000
  USD: US$ 300.000.000
  USDT: US$ 30.000.000 (working capital em trânsito)

Próximos 30 dias:
  Pagamentos USD: US$ 250.000.000 (leasing + combustível + manutenção)
  Recebimentos USD: US$ 50.000.000 (rotas internacionais)
  Exposição líquida USD: -US$ 200.000.000
```

**Primeira decisão do dia**: como pagar US$ 250mi no exterior gastando o menor custo possível, com risco controlado e dentro da lei?

---

## 2. Passo 1 — Rail Comparator: Qual Trilho é Mais Barato?

O sistema começa comparando os **6 trilhos elegíveis** para pagamento cross-border:

### Cenário: Pagar US$ 10mi (lote típico de leasing)

O Rail Comparator calcula **custo total all-in** para cada trilho:

| Trilho | Spread + Tarifa | IOF | Gas | Custo Total | % do Valor |
|--------|----------------|-----|-----|-------------|------------|
| **Wire (Swift)** | Spread FX 2,5% (R$ 1.547.500) + tarifa US$ 40 (R$ 248) | 0,38% (R$ 235.220) | — | **R$ 1.782.968** | **~2,88%** |
| **USDC Polygon** | On-ramp 0,3% (R$ 185.700) + Off-ramp 0,3% (US$ 30.000 ≈ R$ 185.700) | 0,38% (R$ 235.220) | ~R$ 0,06 (Polygon) | **R$ 606.620** | **~0,98%** |
| **USDT Polygon** | On-ramp 0,5% (R$ 309.500) + Off-ramp 0,3% (R$ 185.700) | 0,38% (R$ 235.220) | ~R$ 0,06 | **R$ 730.420** | **~1,18%** |
| **USDC ERC-20** | On-ramp 0,3% + Off-ramp 0,3% | 0,38% | Gas ETH ~R$ 62 | **R$ 606.682** | **~0,98%** |
| **USDT ERC-20** | On-ramp 0,5% + Off-ramp 0,3% | 0,38% | Gas ETH ~R$ 62 | **R$ 730.482** | **~1,18%** |

> **Resultado**: USDC (qualquer rede) custa **R$ 606.620** vs. Wire **R$ 1.782.968** — economia de **~66% por transação**.

### A Conta que o Mercado Ignora

O Wire (Swift) tem spread FX embutido que a mesa de tesouraria raramente enxerga em linha separada. O banco cotou 6,19 PTAX mas liquidou a 6,34 — essa diferença de 2,5% é o maior custo. O stablecoin **dribla o spread FX** porque a conversão BRL→USDT acontece no mercado cripto, onde o prêmio é ~0,3-0,5%.

**A arbitragem regulatória**: stablecoin não passa pelo sistema de câmbio tradicional. O custo não é "cripto ser mais eficiente" — é que o IOF de câmbio (0,38% + spread) incide sobre menos componentes. A BCB 561, em out/2026, vai fechar essa porta.

---

## 3. Passo 2 — Compliance Filter: É Legal?

Antes de apertar qualquer gatilho, o sistema roda o **Compliance Filter**:

```
✅ BCB 519 (ativos virtuais como investimento exterior): OK
✅ BCB 520 (segregação patrimonial): OK — custodiante com segregação
✅ BCB 521 (KYC/AML): OK — fluxo abaixo de R$ 500k por transação, ou KYC completo
⚠️ BCB 561 (proibição stablecoin em eFX): VIGENTE A PARTIR DE OUT/2026
   → Hoje: permitido. Prazo: ~3 meses de janela restante.
```

O sistema gera um **alerta**:

```
┌─────────────────────────────────────────────────────┐
│ ⚠️  BCB 561 entra em vigor em out/2026              │
│ A arbitragem via stablecoin será desligada para eFX │
│ Prazo restante para usar o trilho: ~90 dias         │
│ Consulte jurídico antes de estruturar fluxo novo    │
└─────────────────────────────────────────────────────┘
```

**Tradução de negócio**: a economia de ~66% expira em out/2026. O plano precisa ter data. Depois disso, o Wire volta a ser a única opção para eFX regulado — a menos que a operação seja estruturada como não-eletrônica (o que o sistema não assessora, pois isso exigiria parecer jurídico).

---

## 4. Passo 3 — Depeg Risk Engine: Dá pra Confiar em Stablecoin Agora?

O tesoureiro olha o **histórico de risco** no dashboard. O Depeg Risk Engine mostra:

```
┌─────────────────────────────────────────────────────┐
│  RISCO ATUAL — USDC                                │
│  VaR 97% (janela 90 dias): -0,08%                   │
│  ES 97%: -0,12%                                     │
│  Classificação: MÉDIO ⚡                             │
│                                                     │
│  RISCO ATUAL — USDT                                │
│  VaR 97%: -0,03%                                    │
│  ES 97%: -0,05%                                     │
│  Classificação: BAIXO ✅                             │
│                                                     │
│  CARTEIRA CONSOLIDADA (70% USDT / 30% USDC)         │
│  VaR carteira: -0,045%                              │
│  ES carteira: -0,071%                               │
│  Classificação: BAIXO ✅                             │
└─────────────────────────────────────────────────────┘
```

### O Que Esses Números Significam (Tradução de Negócio)

| Métrica | Tradução |
|---------|----------|
| VaR 97% = -0,08% | "97% das horas dos últimos 90 dias, a pior perda da stablecoin não passou de 0,08%. Só 3% das horas foram piores que isso." |
| ES 97% = -0,12% | "Quando a perda foi maior que 0,08%, a perda média foi de 0,12%." |

**Na prática**: para uma posição de US$ 30mi em USDC, o ES de -0,12% significa que, no pior cenário (cauda de 3%), a perda média esperada é de US$ 36.000 — valor pequeno perto da economia de ~R$ 1,1mi por transação.

### E Se o ES Disparar?

O gráfico histórico do dashboard tem **spikes documentados**:

| Data | Evento | Var 97% USDC | ES 97% | O que aconteceu |
|------|--------|-------------|--------|-----------------|
| Mar/2023 | SVB Crash | -4,2% | -11,5% | USDC caiu a US$ 0,88 |
| Mai/2022 | UST Collapse | -1,8% | -3,2% | Contágio no mercado |
| 11-15 Mar/2023 | Janela crítica | -12,0% | -24,0% | Pior momento do SVB |

**Se você é CFO e vê ES = 24%**:
- A posição de US$ 30mi em USDC pode perder **US$ 7,2mi** no pior cenário
- Ação imediata: reduz alocação USDC, migra para USDT (que não desancorou no SVB), ou aciona wire emergencial
- O sistema **não executa** a realocação — ele informa a decisão. A execução é com a mesa de tesouraria.

---

## 5. Passo 4 — Liquidity Optimizer: Onde Colocar o Caixa?

Com o risco classificado como **BAIXO**, o Liquidity Optimizer calcula a alocação ideal:

### Entrada
```
BRL disponível: R$ 4.000.000.000
DCOH alvo: 60 dias → R$ 3.000.000.000 (reserva de cash)
Excedente: R$ 1.000.000.000
Cap de política stablecoin: 5% do caixa total = R$ 200.000.000
```

### Alocação Recomendada

```
RESERVA DE CASH (CASH-ONLY — stablecoin NÃO entra):
  Tier 1 (Imediato — 20% da reserva): R$ 600.000.000 → Conta remunerada + PIX
  Tier 2 (Curto prazo — 30%): R$ 900.000.000 → CDB com liquidez D+1
                Total reserva: R$ 3.000.000.000 (75% do caixa)

WORKING CAPITAL NO TRILHO:
  Tier 3 — Giro cross-border:
    USDT Polygon: US$ 15.000.000 (R$ 93.000.000) — ~47% do cap
    USDC Polygon: US$ 10.000.000 (R$ 62.000.000) — ~31% do cap
    USDC ERC-20:  US$ 5.000.000  (R$ 31.000.000) — ~16% do cap
                Total: US$ 30.000.000 (R$ 186.000.000) — ~6% acima do cap

⚠️ Posição atual em USDT/USDC (R$ 186.000.000) supera cap de política (R$ 200.000.000)
   → Violação de 6% do limite aprovado pelo board
   → Redução necessária: ~R$ 14.000.000 em stablecoin
```

### Os 3 Tetos em Ação

```
teto_real = min(
    necessidade_de_giro,           # US$ 30mi (R$ 186mi) — quanto precisa estar no trilho
    cap_de_política,               # 5% do caixa total ≈ R$ 200mi — limite de board
    teto_de_depeg,                 # VaR atual -0,045% → teto relaxado (risco baixo)
    1 - fração_de_reserva          # 100% - 75% (reserva) = 25% do caixa ≈ R$ 1bi
)
→ Teto vigente: R$ 186mi (limitado pela necessidade real de giro, não pelo board nem pelo VaR)
```

**O valor do haircut de liquidez ES**: se o ES fosse alto (ex.: -11,5% no SVB), o sistema aplicaria `valor_liquido = US$ 30mi × (1 - 0,115) = US$ 26,55mi` — o valor de liquidez da posição cairia em US$ 3,45mi. Esse desconto apareceria no dashboard como "liquidez ajustada ao risco".

---

## 6. Passo 5 — Custo de Carrego: Quanto Custa Manter Caixa Parado?

O 3º pilar calcula o **custo de oportunidade** da reserva de cash que está parada:

### Cenário Atual

```
Reserva de cash: R$ 3.000.000.000
Yield atual: 0% (conta corrente não remunerada)
CDI: 13,15% a.a.
T-bill: 4,50% a.a.

Custo de carrego ANUAL:
  BRL: R$ 3.000.000.000 × (13,15% - 0%) = R$ 394.500.000/ano
  USD: US$ 300.000.000 × (4,50% - 0%) = US$ 13.500.000/ano
```

### O Trade-off (O Debate que o Sistema Força)

```
┌─────────────────────────────────────────────────────────────────┐
│  Quanto a empresa PERDE por manter caixa conservadoramente?     │
│                                                                 │
│  Economia anual usando stablecoin no trilho: ~R$ 12.000.000     │
│  Custo de carrego da reserva:              ~R$ 394.500.000      │
│                                                                 │
│  A grande perda NÃO está no trilho errado —                     │
│  está na reserva de cash improdutiva.                           │
│                                                                 │
│  Se 10% da reserva fosse alocada em CDB líquido (100% CDI):     │
│  → Recupera R$ 39.450.000/ano — 3x a economia do trilho.       │
└─────────────────────────────────────────────────────────────────┘
```

**Insight de negócio fundamental**: o maior vazamento financeiro não é a escolha entre Wire e USDC. É **manter R$ 3bi parados em conta corrente**. O StableTreasury expõe esse custo — mesmo que a ação corretiva (remunerar a reserva) esteja fora do escopo do sistema (o ADR-0010 documenta isso conscientemente).

---

## 7. O Ciclo Completo — A Rotina Semanal

### Segunda-feira 09:00 — Reunião de Tesouraria

O tesoureiro abre o dashboard e roda o ciclo completo:

```
┌─────────────────────────────────────────────────────────┐
│  STABLETREASURY — RESUMO EXECUTIVO                      │
│  Semana de 14/jul/2026                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. TRILHO RECOMENDADO: USDC Polygon (R$ 606.620 lote)  │
│     vs. Wire (R$ 1.782.968) → economia R$ 1.176.348    │
│                                                         │
│  2. RISCO: BAIXO (VaR -0,045%)                          │
│     Posição USDT/USDC dentro do cap de política         │
│     Haircut ES: US$ 2,13mi (liquidez ajustada)          │
│                                                         │
│  3. COMPLIANCE: OK (BCB 561 ainda não vigente)          │
│     Janela restante: ~90 dias                           │
│                                                         │
│  4. OTIMIZADOR: Alocação recomenda reduzir              │
│     USDC ERC-20 em US$ 2mi (gas caro desnecessário)     │
│     Migrar para USDC Polygon (gas ~R$ 0,06)             │
│                                                         │
│  5. CUSTO DE CARREGO: R$ 1.080.821/semana               │
│     (R$ 394,5mi/ano ÷ 52 semanas × 75% da reserva       │
│      que poderia estar rendendo)                        │
│                                                         │
│  ▶️ Decisão do dia:                                      │
│     Pagar lote de leasing via USDC Polygon               │
│     Redistribuir US$ 2mi de ERC-20 para Polygon          │
│     Agenda com CFO: viabilidade de CDB para reserva     │
└─────────────────────────────────────────────────────────┘
```

### O Fluxo Real de Dados que Torna Isso Possível

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  DefiLlama    │────►│                  │     │              │
│  (preços      │     │  depeg_risk.py   │     │  Dashboard   │
│   históricos) │     │  (VaR/ES/faixa)  │────►│  (5 abas)    │
└──────────────┘     └────────┬─────────┘     │              │
                              │                │              │
┌──────────────┐     ┌────────▼─────────┐     │              │
│  CoinGecko   │     │  otimizador.py    │     │  Tesoureiro  │
│  (preço BRL  │────►│  (3 tetos +       │────►│  lê, decide, │
│   on-ramp)   │     │   haircut ES)     │     │  executa     │
└──────────────┘     └────────┬─────────┘     │  fora do     │
                              │                │  sistema     │
┌──────────────┐     ┌────────▼─────────┐     │              │
│  BCB SGS     │     │  compliance.py    │     │              │
│  (PTAX)      │────►│  (BCB 519-561)    │────►│              │
└──────────────┘     └──────────────────┘     └──────────────┘
```

**Importante**: o sistema é um **motor de decisão**, não de execução. Ele informa, compara, alerta — mas quem aperta o gatilho (ordem de pagamento, swap, câmbio) é a mesa de tesouraria, nos sistemas deles.

---

## 8. O Cenário de Estresse — E Se Acontecer Outro SVB?

Digamos que, em agosto/2026, um banco emissor de USDC reporta problemas de reserva. O dashboard reage em **tempo real**:

### Hora 0 — Evento

```
🚨 ALERTA: USDC caindo abaixo de US$ 0,99
   VaR USDC: -0,08% → -0,35% (subiu 4x em 2 horas)
   ES USDC: -0,12% → -0,89%
```

### Hora 6 — Cenário Médio

```
⚠️ RISCO ALTO
   USDC a US$ 0,95
   VaR: -1,2%
   ES: -4,7%
   
   Haircut ES na posição USDC (US$ 15mi):
   → Valor líquido: US$ 15mi × (1 - 0,047) = US$ 14,3mi
   → Perda estimada em cenário de cauda: US$ 705.000
```

### Hora 24 — Pior Cenário (como SVB)

```
🔴 CRISE — USDC a US$ 0,88
   VaR: -12,0%
   ES: -24,0%
   
   Haircut ES: US$ 15mi × (1 - 0,24) = US$ 11,4mi
   Perda na posição: US$ 1,8mi (já realizada)
   
   Ações sugeridas pelo sistema:
   1. ⛔ Parar de comprar USDC
   2. 🔄 Migrar pagamentos programados para USDT ou Wire
   3. 📊 Reportar perda à auditoria
   4. 📋 Acionar plano de contingência (RCF)
```

### A Lição do SVB (Mar/2023)

**USDC caiu a US$ 0,88 — USDT manteve US$ 0,998.** O VaR/ES capturou isso? Sim. O gráfico histórico mostra o spike exato:

![SVB spike aparece no backtest](o dado da DefiLlama de mar/2023 alimenta o VaR/ES e o gráfico de histórico de risco — o evento SVB está no dado de treino)

**O que o CFO da Azul faria na prática em mar/2023:**
- Perdeu US$ 1,8mi de US$ 15mi expostos em USDC
- Mas economizou ~R$ 8mi no trimestre usando stablecoin vs. Wire
- Saldo líquido: ainda positivo, mas o susto mostrou que **diversificar entre USDC e USDT** mitiga o risco (USDT não desancorou)
- O sistema hoje recomenda 70% USDT / 30% USDC exatamente por isso — o VaR histórico embute essa lição

---

## 9. A Janela de Arbitragem Regulatória — BCB 561

### O Relógio Regulatório

```
OUT/2025 ───────────────────────────────────► OUT/2026 ──►
         │                                    │
         │  BCB 561 publicada                 │  BCB 561 vigente
         │  Stablecoin AINDA permitida        │  Stablecoin PROIBIDA
         │  para eFX                          │  para eFX
         │                                    │
         │  Economia ~66% vs. Wire            │  Retorno ao Wire
         │  disponível                        │  (custo 2,88%)
         │                                    │
         └───▲───▲───▲───▲───▲───▲───▲───────┘
             │   │   │   │   │   │   │
         HOJE (jul/2026): ~90 dias de janela
```

### O Dilema do Tesoureiro

```
Se estruturo fluxo estável em stablecoin agora:
  + Economia de ~R$ 1,1mi/mês por lote de US$ 10mi
  - Risco de depeg (US$ 1,8mi perdido no SVB)
  - Risco regulatório: BCB 561 fecha em out/2026

  Custo de migrar de volta para Wire: ~R$ 100.000 (setup bancário)
  Custo de NÃO usar stablecoin: R$ 1,1mi/mês × 3 meses = R$ 3,3mi

  ▶️ Decisão racional: usar via USDT (menos risco de depeg que USDC)
     com plano de saída para Wire em set/2026.
     Ganho líquido estimado nos 3 meses: ~R$ 3,3mi × (1 - riscos)
```

---

## 10. ROI — A Conta Final (12 Meses)

### Receitas (Economias)

| Fonte | Valor Anual |
|-------|-------------|
| Economia em 12 lotes de US$ 10mi (USDC vs. Wire) | R$ 14.123.664 |
| Menos: custo operacional do sistema (Streamlit Cloud) | -R$ 0 (free tier) |
| Menos: custo de dados (APIs gratuitas) | -R$ 0 |
| **Economia bruta** | **R$ 14.123.664** |

### Riscos

| Risco | Probabilidade | Custo Esperado |
|-------|---------------|----------------|
| Depeg moderado (USDC -5%) 1x no ano | 30% | US$ 225.000 (haircut ES) |
| Depeg severo (USDC -12%) 1x a cada 3 anos | 10% | US$ 900.000 |
| Perda regulatória (BCB 561 + multa) | 5% | US$ 500.000 |
| **Custo esperado total** | | **~US$ 567.500/ano** |

### ROI Líquido

```
Economia anual: R$ 14.123.664
Custo de risco esperado: R$ 3.519.360 (US$ 567.500 × 6,20)
─────────────────────────────────────────────────
Ganho líquido esperado: R$ 10.604.304/ano

vs. Custo de implementar (2 semanas de engenharia): ~R$ 50.000
→ ROI de ~21.000% no primeiro ano
```

---

## 11. Resumo para Diferentes Públicos

### Para o CFO (1 Parágrafo)

"StableTreasury vai te economizar ~R$ 14 milhões por ano trocando Wire por USDC nos pagamentos de leasing e combustível, com risco de desancoragem mapeado em tempo real. Você vê no dashboard se a stablecoin está segura hoje, quanto custa cada trilho, e quando a BCB 561 vai fechar essa janela. A decisão final é sua — o sistema só informa."

### Para o CIO (1 Parágrafo)

"Quatro módulos independentes em Python + Streamlit: Rail Comparator (custo all-in por trilho com spread real de on/off-ramp), Depeg Risk Engine (VaR/ES 97% em janela horária de 90 dias via DefiLlama), Liquidity Optimizer (alocação com 3 tetos simultâneos e haircut ES), Compliance Filter (BCB 519-561). SQLAlchemy com repositório agnóstico de dialeto. Sem autenticação, sem execução real de transações — motor de decisão puro."

### Para o Board (3 Tópicos)

1. **Economia**: ~66% por transação cross-border vs. Wire tradicional
2. **Risco**: VaR/ES quantifica a chance de desancoragem em tempo real; SVB-2023 aparece no dado
3. **Regulatório**: BCB 561 fecha a janela em out/2026 — o projeto mede o prazo de validade da arbitragem
