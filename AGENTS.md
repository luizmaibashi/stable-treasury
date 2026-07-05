# AGENTS.md — StableTreasury

> **Projeto**: Motor de decisão para fintechs compararem trilhos de pagamento B2B.
> **Stack**: Python · Streamlit · CoinGecko API · Etherscan API · BCB SGS

---

## Mapa do projeto

- `src/comparador.py` — Módulo 1: Rail Comparator (custo de cada trilho)
- `src/compliance.py` — Módulo 2: Compliance Filter (BCB 519-521-561)
- `src/otimizador.py` — Módulo 3: Liquidity Optimizer (alocação de caixa)
- `src/iof_tabela.py` — Tabela de alíquotas IOF vigentes
- `src/coletor_precos.py` — Coleta de preços on-chain (CoinGecko, Etherscan)
- `src/depeg_risk.py` — Depeg Risk Engine: VaR/ES sobre histórico de peg (DefiLlama), faixas de risco
- `src/db.py` — Schema SQLAlchemy (fonte única): tabelas `peg_prices` e `risk_snapshots`
- `src/repositorio.py` — Camada de persistência agnóstica de dialeto (SQLite/Postgres)
- `src/ingestao.py` — Backfill histórico paginado + geração de snapshots de risco (backtest)
- `app.py` — Dashboard Streamlit (5 tabs, incl. Histórico de Risco)
- `docker-compose.yml` — Postgres 16 local para desenvolvimento
- `data/raw/iof_aliquotas.yaml` — Alíquotas IOF por tipo de operação
- `docs/adr/` — Architecture Decision Records

---

## Linguagem Ubíqua

| Termo | Significado |
|-------|-------------|
| **Trilho (Rail)** | Canal de pagamento: Wire, PIX, USDT, USDC |
| **Rail Comparator** | Comparador de custo total entre trilhos para uma dada fatura |
| **Custo total** | Spread FX + tarifa fixa + IOF + gas fee (se aplicável) |
| **Gas fee** | Taxa de rede blockchain para transação on-chain |
| **Spread FX** | Diferença entre taxa de câmbio comercial e a taxa praticada |
| **IOF** | Imposto sobre Operações Financeiras (alíquota por decreto federal) |
| **BCB 561** | Resolução que proíbe liquidação via stablecoin para eFX (out/2026) |
| **Poupador Assustado** | (herdado do Shadow FX) Comprador legítimo de USDT como hedge |
| **Liquidity Optimizer** | Motor de alocação entre BRL/USDT/USD, baseado em Depeg Risk Engine (VaR/ES) — ADR-0003 |
| **eFX** | Electronic Foreign Exchange — sistema regulado de câmbio digital |
| **Depeg** | Desvio do preço de uma stablecoin em relação à paridade 1:1 com o USD |
| **VaR (Value at Risk)** | Perda máxima esperada, com dado nível de confiança, num horizonte de tempo |
| **Expected Shortfall (ES)** | Perda média esperada nos piores cenários além do VaR (cauda da distribuição) |
| **Proof-of-Reserve** | Prova on-chain/atestada de que o emissor da stablecoin possui reservas equivalentes ao supply emitido |
| **Attestation** | Relatório público (Circle/Tether) que declara composição das reservas que lastreiam a stablecoin |
| **Backfill** | Carga inicial de histórico no banco (2022→hoje) via ingestão paginada |
| **Risk Snapshot** | Registro de risco (ES/VaR/faixa/teto) calculado num momento; série alimenta o gráfico histórico |
| **Backtest** | Reconstrução do risco ao longo do tempo (ES rolante) sobre preço histórico real |
| **Dev/prod parity** | Mesmo motor de banco (Postgres) local e em produção, evitando surpresa de dialeto |

---

## Regras de engenharia

- **Custo zero**: todas as fontes de dados são APIs gratuitas
- **IOF como parâmetro**: alíquotas em YAML, não hardcoded
- **Sem dependência do Shadow FX**: cada projeto se sustenta sozinho
- **Dados on-chain reais**: CoinGecko (preço), Etherscan (gas fee estimado)
- **Streamlit apenas**: sem API REST (escopo de portfolio)

---

## ADRs registrados

| ADR | Decisão | Status |
|-----|---------|--------|
| 0001 | Fontes de dados gratuitas (CoinGecko + Etherscan + BCB); estendido pelo 0003 (DefiLlama) | Accepted |
| 0002 | Arquitetura Streamlit + módulos Python | Proposed |
| 0003 | Pivot Liquidity Optimizer → Depeg Risk Engine + infra Postgres | Accepted |
| 0004 | Parâmetros e calibração do Depeg Risk Engine (faixas, confiança 97%, janela 90d) | Accepted |
| 0005 | Persistência com SQLAlchemy (fonte única) + Postgres em Docker | Accepted |

---

## Débitos técnicos conhecidos

1. Spread bancário é estimado por faixa pública (não cotação ao vivo)
2. Faturas B2B são sintéticas (mock), não dados reais de parceiro
3. Sem API REST (só dashboard + módulos Python)
4. BCB 561 implementada como regra determinística (sem interpretação jurídica)
5. ~~Liquidity Optimizer usa heurística fixa (50/30/20) sem base quantitativa~~ **RESOLVIDO** — `src/depeg_risk.py` calcula VaR/ES sobre histórico real (DefiLlama) e classifica risco em faixas calibradas com eventos reais (USDC-SVB, UST); teto de alocação em `src/otimizador.py` deriva desse cálculo, não mais fixo. Ver ADR-0003.
6. ~~Projeto é 100% stateless (sem histórico persistido)~~ **RESOLVIDO** — persistência via SQLAlchemy + Postgres em Docker (ADR-0005); histórico 2022→hoje ingerido, série de risco (backtest) persistida.
7. Depeg Risk Engine mede risco só sobre USDC (`usd-coin`) e aplica o teto ao total em stablecoin; USDT tem perfil de reserva/attestation distinto. Ideal: teto ponderado pela composição real da carteira (USDT vs USDC). Simplificação consciente, documentada em `app.py`.
8. VaR/ES usa granularidade diária (DefiLlama `period=1d`), que suaviza o mínimo intra-dia real (ex: USDC tocou 0,8767 hourly em mar/2023, mas a série diária registra ~0,96). O risco de cauda real é subestimado — mitigável usando `period=1h` em janelas de stress.

## Escopo negativo (ADR-0003)

- Sem autenticação/multi-tenant (single-tenant, demo de portfolio)
- Sem execução real de transação (nunca integra custodian/exchange real)
- Sem assessoria jurídica ou fiscal real (compliance filter é interpretação própria, com disclaimer)
- Sem apuração de IR/renda (só IOF)
- Uma tesouraria simulada por vez
