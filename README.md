# 🏦 StableTreasury

**Motor de decisão de tesouraria cross-border: mede a arbitragem do trilho stablecoin, o risco de depeg de usá-la e o custo de não usar o caixa — com rigor de mesa, não de tutorial.**

> Existe uma janela de arbitragem de **~90%** em pagamentos cross-border via stablecoin — e parte dela tem **data de expiração regulatória** (Resolução BCB 561, vigência 1º/out/2026, que proíbe stablecoin como liquidação em operações formais de **eFX**). Este projeto mede os três lados dessa decisão ao mesmo tempo: **quanto se economiza**, **quanto risco se corre**, e **quanto custa o caixa parado** — e o Compliance Filter já bloqueia corretamente a operação restrita, meses antes da regra valer.
>
> A 561 é escopada a eFX — a arbitragem **persiste** fora desse regime formal, e o Depeg Risk Engine (o motor central) não tem prazo de validade nenhum. Validação completa em [`docs/val-loop/bcb561-prazo/`](docs/val-loop/bcb561-prazo/).

---

## O problema

Uma tesouraria que paga no exterior — fintech, companhia aérea (leasing/combustível em USD), importador — precisa responder, todo dia:

1. **Qual trilho custa menos?** (PIX, Wire/SWIFT, USDT, USDC)
2. **Isso é legal?** (Resoluções BCB 519/520/521/561)
3. **Posso confiar na stablecoin agora?** (risco de depeg)
4. **Como alocar o caixa?** (reserva, hedge, giro)
5. **O caixa parado está me custando quanto?** (custo de oportunidade)

Não existe ferramenta que junte as cinco. StableTreasury junta.

---

## O protagonista: Depeg Risk Engine

O coração do projeto **não** é o comparador de custos — é o motor de risco. Ele calcula **VaR / Expected Shortfall** (a métrica que Basel III/FRTB adotou para risco de mercado) sobre o **histórico real de peg** das stablecoins (DefiLlama, 2022→hoje).

**A validação mais forte:** o spike do **colapso do Silicon Valley Bank (mar/2023)** — quando a Circle tinha US$ 3,3 bi das reservas do USDC presos no SVB e a moeda despegou para ~US$ 0,88 — **aparece sozinho** no gráfico histórico, sem nenhum hardcode de data. *O modelo descobre a crise porque o preço real caiu naquela janela.*

📄 **[Deep Dive completo do motor de risco →](docs/DEEP_DIVE_DEPEG_ENGINE.md)** (o que é ES, por que 90d/97%, os spikes reais, o que um CFO faz)

---

## Os 3 pilares (tesouraria corporativa de verdade)

Modelado segundo a estrutura clássica de tesouraria — **não** como um "dashboard de cripto":

| Pilar | O que faz | Rigor |
|-------|-----------|-------|
| **Cash Management** | Rail Comparator: custo all-in por trilho, segmentado por caso de uso (doméstico × cross-border) | Custo do trilho stablecoin inclui on-ramp (prêmio real) + gas + off-ramp; slippage medido no **order book real** (Binance VWAP) |
| **Risk / Hedging** | Depeg Risk Engine: VaR/ES sobre carteira real (USDC+USDT ponderados), série **horária** | Correlação emerge do dado; cauda de ~65 amostras; captura mínimo intra-dia real (0,8767) |
| **Capital Markets & Funding** | Custo de carrego da reserva de cash (BRL vs CDI, USD vs T-bill) | Taxas **ao vivo** (BCB SGS + US Treasury); reserva é **cash** — stablecoin não é caixa equivalente (US GAAP/IFRS, ASU 2023-08) |

**Decisão-chave de conformidade:** a reserva de emergência é **cash-only**. Stablecoin entra apenas como **capital de giro em trânsito** no trilho, com teto triplo (necessidade de fluxo / cap de política 5% / teto de depeg) e haircut pelo ES. Perfil de referência ancorado em **Azul S.A. FY2024** (aérea com passivo em USD — caso de livro-texto de tesouraria cambial).

---

## Stack

`Python` · `Streamlit` (dashboard) · `Polars` (dados) · `NumPy` (VaR/ES) · `SQLAlchemy` + `PostgreSQL` (histórico) · APIs gratuitas: **CoinGecko**, **DefiLlama**, **BCB SGS**, **US Treasury**, **Binance** (order book).

Custo zero de operação — todas as fontes de dado são públicas e gratuitas.

---

## Como rodar

```bash
# 1. Dependências
pip install -r requirements.txt

# 2. Banco local (Postgres em Docker)
docker compose up -d

# 3. Popular o histórico (schema + backfill 2022→hoje + backtest de risco)
python -m scripts.seed_db

# 4. Dashboard
streamlit run app.py
```

Para produção sem Docker, aponte `DATABASE_URL` para um Postgres gerenciado (ex: Neon free tier) — só a variável de ambiente muda, o código não (ver [ADR-0006](docs/adr/0006-deploy-publico-streamlit-neon.md)).

```bash
# Testes (73)
python -m pytest -q
```

---

## Arquitetura

```
coletor_precos.py   ← única porta de rede (CoinGecko, DefiLlama, BCB, Treasury, Binance)
      │
      ├── comparador.py    (Rail Comparator + compliance.py: filtro BCB 561)
      ├── depeg_risk.py    (VaR/ES — o núcleo) ←── ingestao.py → repositorio.py → db.py
      ├── otimizador.py    (alocação: reserva cash + giro stablecoin)
      └── custo_carrego.py (3º pilar: opportunity cost da reserva)
      │
    app.py  (Streamlit — 5 abas)
```

**Princípios:** todo I/O de rede isolado num módulo (resto testável sem rede); o ES é o único acoplamento matemático real (vira teto de alocação **e** haircut de liquidez).

📄 **[Aula técnica completa (ponta a ponta) →](docs/AULA_TECNICA_COMPLETA.md)** · **[ADRs (decisões) →](docs/adr/)** · **[Auditoria técnica →](docs/audit/)**

---

## O que este projeto assume abertamente

Rigor é também saber o que **não** se sabe. Débitos técnicos, premissas e escopo negativo estão documentados em [`AGENTS.md`](AGENTS.md) — incluindo a decisão consciente de **não** transformar o cap de política de risco (5%) em "medição": é uma decisão normativa de board, não uma quantidade de mercado. Fingir uma fórmula ali seria o "número mágico" que o projeto combate.

---

*Projeto de portfolio — não é assessoria jurídica, fiscal ou de investimento. Nenhuma transação real é executada.*
