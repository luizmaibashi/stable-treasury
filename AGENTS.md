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
- `src/perfil_referencia.py` — perfil de tesouraria do demo, âncora de escala em dado real (Nubank FY2025) vs. premissa ilustrativa (ADR-0009)
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
| **Neon** | Provedor de Postgres gerenciado (nuvem), free tier — usado em produção pra manter dev/prod parity do ADR-0005 sem custo |
| **Cold start (Neon)** | Free tier pausa o banco após inatividade; primeira consulta depois da pausa demora alguns segundos a mais pra "acordar" |
| **DATABASE_URL** | Variável de ambiente que aponta pro banco (Docker local em dev, Neon em prod) — trocar só ela muda o ambiente, código não muda |
| **Opportunity Cost** | Rendimento que o caixa alocado em stablecoin deixa de ganhar por ficar parado; card do dashboard compara % alocado pelo Optimizer vs. yield de protocolo de referência (ADR-0007) |
| **Yield (APY)** | Taxa de rendimento anual de um protocolo DeFi (ex: Aave), consultada via DefiLlama `/yields` — só leitura de dado público, sem execução/depósito real |
| **Slippage heurístico** | Acréscimo de custo estimado por faixa de volume no Rail Comparator, aproximando perda de liquidez em conversões grandes — não é modelo de order book real (ADR-0007, débito técnico #11) |
| **Caso de uso** | Segmento do pagamento: `domestico` (BRL→BRL, só PIX) ou `cross_border` (converte BRL↔USD: Wire/USDT/USDC). Comparação de trilhos só é válida dentro do mesmo caso de uso (ADR-0008) |
| **On-ramp / Off-ramp** | Entrada (BRL→stablecoin, prêmio real de mercado) e saída (stablecoin→USD, 0,3% fixo) do trilho cripto — o custo de conversão que o modelo antigo ignorava (ADR-0008) |
| **DCOH (days cash on hand)** | Dias de opex cobertos pelo caixa; base corporativa pra dimensionar reserva (default 60d), no lugar de "meses de despesa" (ADR-0009) |
| **Working capital no trilho** | Stablecoin tratada como capital de giro EM TRÂNSITO no trilho cross-border (≈ fluxo × dias de settlement), não investimento de reserva (ADR-0009) |
| **Cash equivalent** | Caixa e equivalentes (depósito à vista, T-bill ≤90d). Stablecoin NÃO é cash equivalent (US GAAP/IFRS, ASU 2023-08) → excluída da reserva de emergência (ADR-0009) |
| **Cap de política** | Limite de sleeve de ativos digitais aprovável por board (1–5%; default 5%) — um dos tetos sobre a stablecoin (ADR-0009) |
| **Haircut de liquidez** | Desconto aplicado ao valor de liquidez da stablecoin pelo ES do Depeg Engine: `valor × (1 − ES)` (ADR-0009) |

---

## Regras de engenharia

- **Custo zero**: todas as fontes de dados são APIs gratuitas
- **IOF como parâmetro**: alíquotas em YAML, não hardcoded
- **Sem dependência do Shadow FX**: cada projeto se sustenta sozinho
- **Dados on-chain**: CoinGecko (preço), Etherscan/PolygonScan (gas fee estimado **quando há API key**; sem key, cai para faixa fixa — não on-chain ao vivo, F6)
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
| 0006 | Deploy público via Streamlit Community Cloud + Neon (estende dev/prod parity do 0005) | Accepted |
| 0007 | Opportunity Cost (yield, DefiLlama) + heurística de slippage por volume; hedge real (put option) rejeitado por violar escopo negativo do ADR-0003 | Accepted |
| 0008 | Modelo de custo honesto do Rail Comparator: spread on/off-ramp no trilho stablecoin + segmentação por caso de uso + religação do filtro eFX (auditoria F1/F2/F7) | Accepted |
| 0009 | Conformidade com tesouraria corporativa: reserva em cash-only (stablecoin não é caixa equivalente), stablecoin como working capital no trilho com teto triplo + haircut ES; âncora de escala Nubank FY2025 | Accepted |

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
9. `var_es_historico` aceita `confianca` fora de [0,1] (ex: 1.5, -0.1) silenciosamente, sem validar — clampa pro mesmo resultado do limite válido. Baixo risco (função interna, nunca exposta a input de usuário), mas sem guarda explícita. Achado no PAVC audit 2026-07-05.
10. `_utc_naive`/`_com_utc` (`src/repositorio.py`) assumem implicitamente que `datetime` sem timezone já está em UTC, sem validar. Se código futuro passar naive em horário local, persiste silenciosamente errado. Achado no PAVC audit 2026-07-05.
11. Heurística de slippage por volume (`comparador.py`, ADR-0007) é aproximação documentada — não modela order book/liquidez real, aplica acréscimo estimado por faixa de valor, mesmo padrão do débito #1 (spread bancário estimado). Não usar como cotação precisa.
12. ~~Custo do trilho stablecoin = só gas (ignora on/off-ramp); PIX domina comparação apples-to-oranges~~ **RESOLVIDO** (ADR-0008) — custo stablecoin = spread on-ramp (prêmio real) + gas + off-ramp (0,3% fixo); comparador segmenta por caso de uso (doméstico/cross-border) e religa o filtro eFX (BCB 561).
13. ~~Otimizador com duas lógicas de alocação inconsistentes; reserva "3 meses" e alvo 50–60% stablecoin fora de conformidade corporativa~~ **RESOLVIDO** (ADR-0009) — alocação única: reserva em cash-only por DCOH, stablecoin como working capital com teto triplo (necessidade/política 5%/depeg) + haircut ES.
14. Off-ramp stablecoin (0,3%, `comparador.py`) é constante conservadora estimada, não medida (ADR-0008). Mesmo status do débito #1.
15. `DIAS_SETTLEMENT` (5) e `CAP_POLITICA_STABLECOIN` (5%) em `otimizador.py` são premissas de política, não medidas (ADR-0009). Configuráveis, documentadas.
16. ES de robustez rasa: janela 90d @ 97% = cauda de 3 amostras (`tamanho_cauda`), estimador sensível a outlier. Exposto na UI como disclaimer (F4); combina com débito #8.
17. Perfil de referência (`perfil_referencia.py`) mistura dado real de escala (Nubank FY2025, com fonte) e premissa de fluxo cross-border (ilustrativa). Cada campo rotulado; Nubank é banco, usado só como âncora de ordem de grandeza (ADR-0009).

## Escopo negativo (ADR-0003)

- Sem autenticação/multi-tenant (single-tenant, demo de portfolio)
- Sem execução real de transação (nunca integra custodian/exchange real)
- Sem assessoria jurídica ou fiscal real (compliance filter é interpretação própria, com disclaimer)
- Sem apuração de IR/renda (só IOF)
- Uma tesouraria simulada por vez

## Pontos de melhoria conhecidos, fora de escopo (ADR-0007)

- **Hedge real (put option DeFi)**: sugerido por revisão externa como extensão do Depeg Risk Engine (medir risco → executar hedge, não só reduzir alocação). Rejeitado: exige custódia/execução real de transação, violando escopo negativo do ADR-0003. Uma versão "fake" (rótulo sem lastro) foi descartada por não agregar informação além do que o Optimizer já comunica.
