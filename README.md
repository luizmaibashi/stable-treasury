# 🏦 StableTreasury

**Produto de decisão pré-pagamento para tesourarias de importadores: transforma uma fatura e cotações recebidas em evidência rastreável para aprovação humana.**

### 🔗 [Ver o dashboard ao vivo](https://stable-treasury-khrmolkmu738evtrxd9aqv.streamlit.app/)

> O primeiro MVP não executa pagamentos, não custodia ativos, não gera cotações e não dá parecer jurídico. Ele compara propostas que a empresa já recebeu, calcula custo total, prazo, impacto no caixa e exposição cambial declarada; também aponta exceções de política. A decisão e a execução continuam humanas e fora da plataforma.

---

## O problema que o MVP resolve

O responsável financeiro de um importador B2B industrial de porte médio, com **4 a 20 pagamentos internacionais por mês** e faturas típicas entre **R$ 100 mil e R$ 2 milhões**, ainda consolida fatura, e-mails de parceiros, planilhas de caixa e políticas internas sob pressão de prazo. Quando a decisão é questionada, a evidência está espalhada.

O StableTreasury organiza uma decisão repetível:

1. Registra a fatura, vencimento, moeda e fluxo previsto.
2. Compara ao menos duas cotações declaradas, com fonte e horário.
3. Mostra o menor custo total, prazo, caixa após pagamento e exposição líquida em USD.
4. Bloqueia recomendação quando há dado ausente, cotação vencida/futura, caixa insuficiente ou exceção de política.
5. Produz uma recomendação apenas quando o caso está pronto para **aprovação humana**.

O teste de valor é objetivo: diante de duas cotações, o dossiê deve explicar em menos tempo a escolha, preservar a origem das premissas e tornar visíveis exceções que uma planilha bem feita pode deixar implícitas.

O [kill gate contra uma planilha bem feita](docs/validation/0001-kill-gate-contra-planilha.md) separa o que já foi provado tecnicamente do que ainda exige uso por um tesoureiro real.

## Para quem — e para quem não é

O foco inicial é o importador B2B industrial médio. Não é um TMS/ERP, mesa de câmbio, banco, corretora, custodiante ou sistema de execução. Integrações, login, multiempresa, geração de cotações, hedge e IA generativa estão explicitamente fora do MVP. A definição verificável está em [`docs/spec/0001-mvp-pacote-decisao-pre-pagamento.md`](docs/spec/0001-mvp-pacote-decisao-pre-pagamento.md).

---

## Laboratório analítico legado

Os módulos abaixo permanecem como laboratório de análise de risco, liquidez e trilhos. Eles não fazem parte da promessa de execução do MVP e não devem ser interpretados como preço ao vivo, aconselhamento ou verificação regulatória.

---

## Depeg Risk Engine

O coração do projeto **não** é o comparador de custos — é o motor de risco. Ele calcula **VaR / Expected Shortfall** (a métrica que Basel III/FRTB adotou para risco de mercado) sobre o **histórico real de peg** das stablecoins (DefiLlama, 2022→hoje).

**A validação mais forte:** o spike do **colapso do Silicon Valley Bank (mar/2023)** — quando a Circle tinha US$ 3,3 bi das reservas do USDC presos no SVB e a moeda despegou para ~US$ 0,88 — **aparece sozinho** no gráfico histórico, sem nenhum hardcode de data. *O modelo descobre a crise porque o preço real caiu naquela janela.*

📄 **[Deep Dive completo do motor de risco →](docs/DEEP_DIVE_DEPEG_ENGINE.md)** (o que é ES, por que 90d/97%, os spikes reais, o que um CFO faz)

---

## Os 3 pilares (tesouraria corporativa de verdade)

Modelado segundo a estrutura clássica de tesouraria — **não** como um "dashboard de cripto":

| Pilar | O que faz | Rigor |
|-------|-----------|-------|
| **Cash Management** | Rail Comparator: custo all-in por trilho, segmentado por caso de uso (doméstico × cross-border) | Custo do trilho stablecoin inclui on-ramp (prêmio real) + gas + off-ramp; slippage medido no **order book real e da moeda certa** (Binance VWAP, USDT e USDC separados); spread do Wire é **parâmetro configurável** (não constante fixa) com **fronteira de indiferença** calculável |
| **Risk / Hedging** | Depeg Risk Engine: VaR/ES sobre carteira real (USDC+USDT ponderados), série **horária** | Correlação emerge do dado; ES(97%) do evento SVB medido ao vivo em 4,18% horário (margem de 0,82pp até o corte de risco); haircut de liquidez tem **piso de ES estressado** contra a proclicidade do VaR histórico |
| **Capital Markets & Funding** | Custo de carrego da reserva de cash (BRL vs CDI, USD vs T-bill) | Taxas **ao vivo** (BCB SGS + US Treasury); reserva é **cash** — stablecoin não é caixa equivalente (US GAAP/IFRS, ASU 2023-08); diferencial CDI−T-bill sinalizado como carry trade cambial, não "dinheiro sem risco" |

**Decisão-chave de conformidade:** a reserva de emergência é **cash-only**. Stablecoin entra apenas como **capital de giro em trânsito** no trilho, com teto triplo (necessidade de fluxo / cap de política 5% / teto de depeg) e haircut pelo ES. Perfil de referência ancorado em **Azul S.A. FY2024** (aérea com passivo em USD — caso de livro-texto de tesouraria cambial). Decisão de hedge cambial usa a **exposição líquida** (recebimento − pagamento), não só "existe recebimento em USD?" — protege perfis com passivo pesado como o da Azul.

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
# Testes (94)
python -m pytest -q
```

---

## Arquitetura

```
coletor_precos.py   ← única porta de rede (CoinGecko, DefiLlama, BCB, Treasury, Binance)
      │
      ├── decisao_pre_pagamento.py (MVP: cotações declaradas → dossiê determinístico)
      ├── comparador.py    (Rail Comparator + compliance.py: filtro BCB 561)
      ├── depeg_risk.py    (VaR/ES — o núcleo) ←── ingestao.py → repositorio.py → db.py
      ├── otimizador.py    (alocação: reserva cash + giro stablecoin)
      └── custo_carrego.py (3º pilar: opportunity cost da reserva)
      │
    app.py  (Streamlit — dossiê pré-pagamento + laboratórios analíticos)
```

**Princípios:** todo I/O de rede isolado num módulo (resto testável sem rede); o ES é o único acoplamento matemático real (vira teto de alocação **e** haircut de liquidez).

📄 **[Aula técnica completa (ponta a ponta) →](docs/AULA_TECNICA_COMPLETA.md)** · **[ADRs (decisões) →](docs/adr/)** · **[Auditoria técnica →](docs/audit/)**

---

## O que este projeto assume abertamente

Rigor é também saber o que **não** se sabe. Débitos técnicos, premissas e escopo negativo estão documentados em [`AGENTS.md`](AGENTS.md) — incluindo a decisão consciente de **não** transformar o cap de política de risco (5%) em "medição": é uma decisão normativa de board, não uma quantidade de mercado. Fingir uma fórmula ali seria o "número mágico" que o projeto combate.

Auditoria mais recente (2026-07-30, [ADR-0012](docs/adr/0012-auditoria-2026-07-30-correcoes.md)): corrigiu um erro de sinal no hedge cambial (recomendava liquidar USD numa exposição líquida SHORT), uma incoerência entre teto e haircut de risco no fallback do motor, e expôs — sem fingir resolver — três limitações estruturais que não têm solução gratuita: a defasagem entre PTAX (D-1) e preço cripto em tempo real, o diferencial de juros CDI×T-bill como carry trade (não "dinheiro grátis"), e a proclicidade do VaR histórico (mitigada com um piso de ES estressado, não eliminada).

---

*Projeto de portfolio — não é assessoria jurídica, fiscal ou de investimento. Nenhuma transação real é executada.*
