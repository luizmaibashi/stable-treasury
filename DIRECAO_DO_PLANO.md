# 🎯 DIREÇÃO DO PLANO — StableTreasury

## O Problema

Tesourarias de fintechs brasileiras precisam decidir:
- Qual **trilho de pagamento** usar (PIX, Wire, USDT, USDC)?
- Quanto **confiar em stablecoin** (risco de depeg)?
- Como **alocar BRL/USDT/USD** de forma segura?

Hoje: sem ferramentas. Tomorrow: **StableTreasury**.

---

## A Solução em 5 Camadas

### 1️⃣ Rail Comparator
**Pergunta:** Qual trilho custa menos?  
**Fórmula:** Spread FX + Tarifa + IOF + Gas Fee  
**Exemplo:** R$ 50k → PIX R$ 0 vs. Wire R$ 3.129 (99,99% economia)

### 2️⃣ Compliance Filter  
**Pergunta:** É legal fazer isso?  
**Regras:** BCB 561 (proíbe stablecoin pra eFX), BCB 520 (KYC), BCB 521 (>R$ 500k)

### 3️⃣ Depeg Risk Engine
**Pergunta:** Posso confiar em stablecoin agora?  
**Método:** VaR/ES sobre histórico real (DefiLlama 2022-2026)  
**Resultado:** "Nos piores 3% dos cenários, você perde até X%"  
**Validação:** SVB-mar-2023 spike aparece automaticamente no gráfico

### 4️⃣ Liquidity Optimizer
**Pergunta:** Como alocar BRL/USDT/USD?  
**Lógica:** Se ES baixo → 60% stablecoin. Se ES alto → 20% stablecoin.

### 5️⃣ Dashboard Streamlit
**5 abas:** Rail | Compliance | Liquidity | Histórico de Risco | Config

---

## A Story que Brilha

**Slide 1:** Tesouraria precisa otimizar alocação de caixa  
**Slide 2:** Solução: VaR/ES quantitativo sobre histórico real  
**Slide 3:** Validação: SVB-2023 spike aparece no gráfico  
**Slide 4:** Resultado: 99,99% economia vs. Wire  
**Slide 5:** Diferencial: Custo zero + regulatório embarcado

---

## 3 Frentes de Execução

| Frente | Objetivo | Status |
|--------|----------|--------|
| **A** | README + Documentação | ⏸️ Aguarda Deep Dive |
| **B** | Depeg Risk Engine Deep Dive | 🚀 COMEÇANDO AGORA |
| **C** | Deploy (Streamlit + Neon) | ⏸️ Aguarda A+B |

---

## O que fazer AGORA (90 min)

### Passo 1: Contexto (5 min)
```bash
cat RETOMA_EM_CASA.md
cat AGENTS.md
```

### Passo 2: Setup (10 min)
```bash
docker compose up -d
python src/ingestao.py
```

### Passo 3: Código (30 min)
```bash
code src/depeg_risk.py
# Foca em: var_es_historico() e classificar_faixa_risco()
```

### Passo 4: Dashboard (20 min)
```bash
streamlit run app.py
# Va na aba "Histórico de Risco" — procura spikes (mar-2023, mai-2022)
```

### Passo 5: Respostas (25 min)
Escreva em markdown:
1. O que é ES?
2. Por quê 90 dias + confiança 97%?
3. Quais datas têm spike? Por quê?
4. Se você é CFO, o que FAZ quando vê ES = 24%?
5. Qual é a story em 3-5 slides?

---

## Outputs Esperados

✅ 5 perguntas respondidas  
✅ 3-5 slides da story capturados  
✅ Compreensão profunda do Depeg Risk Engine  
✅ Pronto pra Frente A (README com narrativa)

---

**Começa agora. Bora brilhar.** 🚀
