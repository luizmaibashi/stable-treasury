# 🏠 RETOMA EM CASA — 2026-07-10

**TL;DR:** Mudou a abordagem. Não é mais "executar spec rápido". É **"entender profundamente antes de contar história"**.

---

## O que mudou

**Antes:** Spec diz → execute Frente A+C → pronto.

**Agora:** Aprenda profundamente → capte a story → aí sim execute com convicção.

Por quê? Sua confissão foi clara: "Arquitetei rápido demais. Preciso refazer focando em entender técnico + negócio pra realmente brilhar."

---

## Retoma em 3 passos

### 1️⃣ Lê isto (5 min)
```
cat PROJETOS/02_PORTFOLIO/stable-treasury/SS_2026-07-10_grill-with-docs-partial.md
```
(Contexto completo do que foi feito + onde parou)

### 2️⃣ Deep Dive (90 min) — ESTA SESSÃO
**Objetivo:** Entender VaR/ES + contar história que brilha.

**Checklist:**
```bash
# Inicia banco local
docker compose up -d

# Abre o código que é o core
code src/depeg_risk.py

# Rodinha a ingestão (se não tiver rodado ainda)
python src/ingestao.py

# Vê o dashboard
streamlit run app.py
# → Vai na aba "Histórico de Risco"
# → Procura os spikes (mar-2023 = SVB, mai-2022 = UST)
```

**Perguntas pra responder (escreve em markdown):**
1. O que é Expected Shortfall (ES)?
2. Por quê calibrar com 90 dias + confiança 97%?
3. Em quais datas tem spike no gráfico histórico? Por quê?
4. Se você é CFO, o que *faz* quando vê ES = 24%?
5. Qual é a story em 3-5 slides que quer contar?

### 3️⃣ Prepara pra próxima sessão
Guarda as respostas (vai ser a base pra escrever README + reordenar abas).

---

## Arquivos-chave pra ter abertos

1. `SS_2026-07-10_grill-with-docs-partial.md` — contexto
2. `src/depeg_risk.py` — o coração do projeto
3. `docs/adr/0003-pivot-depeg-risk-engine.md` — por quê esse pivot
4. `docs/adr/0004-parametros-depeg-risk-engine.md` — como foi calibrado
5. `AGENTS.md` — Linguagem Ubíqua

---

## Dúvidas?

Se travar, volta pro `SS_2026-07-10_grill-with-docs-partial.md` — lá tem o contexto completo + links.

**Bora brilhar.** 🚀
