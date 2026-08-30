# AGENTS.md — StableTreasury

> **Projeto**: Portfólio/laboratório de tesouraria e risco; inclui demonstração de decisão pré-pagamento determinística.
> **Stack**: Python · Streamlit · CoinGecko API · Etherscan API · BCB SGS

> **Status do posicionamento comercial (2026-08-30):** encerrado pelo gate documental `docs/validation/0003-varredura-documental-mercado-e-concorrencia.md`. O dossiê pré-pagamento é artefato técnico, não produto validado; não adicionar integrações, IA, execução ou alegações comerciais sob essa hipótese.

---

## Mapa do projeto

- `src/comparador.py` — Módulo 1: Rail Comparator (custo de cada trilho)
- `src/decisao_pre_pagamento.py` — MVP: compara cotações declaradas e gera dossiê determinístico; não consulta mercado nem executa pagamentos
- `src/compliance.py` — Módulo 2: Compliance Filter (BCB 519-521-561)
- `src/otimizador.py` — Módulo 3: Liquidity Optimizer (alocação de caixa)
- `src/iof_tabela.py` — Tabela de alíquotas IOF vigentes
- `src/coletor_precos.py` — Coleta de preços on-chain (CoinGecko, Etherscan)
- `src/depeg_risk.py` — Depeg Risk Engine: VaR/ES sobre histórico de peg (DefiLlama), faixas de risco
- `src/perfil_referencia.py` — perfil de tesouraria do demo, âncora de escala em dado real (Azul S.A. FY2024, passivo em USD) vs. premissa ilustrativa (ADR-0009/0011)
- `src/custo_carrego.py` — 3º pilar (Capital Markets & Funding): custo de oportunidade da reserva de cash (BRL vs CDI, USD vs T-bill) — ADR-0010
- `src/db.py` — Schema SQLAlchemy (fonte única): tabelas `peg_prices` e `risk_snapshots`
- `src/repositorio.py` — Camada de persistência agnóstica de dialeto (SQLite/Postgres)
- `src/ingestao.py` — Backfill histórico paginado + geração de snapshots de risco (backtest)
- `app.py` — Dashboard Streamlit (dossiê pré-pagamento + abas analíticas)
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
| **Decisão pré-pagamento** | Escolha humana de como liquidar uma fatura internacional, antes de instruir qualquer parceiro financeiro |
| **Pacote de decisão** | Artefato rastreável com fatura, cotações, premissas, cálculo, alertas e recomendação condicionada; não executa nem aprova o pagamento |
| **Cotação anexada** | Preço e prazo recebidos de parceiro autorizado, com fonte e horário declarados; insumo do cálculo, não cotação gerada pelo StableTreasury |
| **Backtest** | Reconstrução do risco ao longo do tempo (ES rolante) sobre preço histórico real |
| **Dev/prod parity** | Mesmo motor de banco (Postgres) local e em produção, evitando surpresa de dialeto |
| **Neon** | Provedor de Postgres gerenciado (nuvem), free tier — usado em produção pra manter dev/prod parity do ADR-0005 sem custo |
| **Cold start (Neon)** | Free tier pausa o banco após inatividade; primeira consulta depois da pausa demora alguns segundos a mais pra "acordar" |
| **Atualização sob demanda** | Na abertura do dashboard, atualiza somente o delta de preço vencido há mais de 24 h; não é cron e não executa backfill automático (ADR-0015) |
| **DATABASE_URL** | Variável de ambiente que aponta pro banco (Docker local em dev, Neon em prod) — trocar só ela muda o ambiente, código não muda |
| **Opportunity Cost** | Rendimento que o caixa alocado em stablecoin deixa de ganhar por ficar parado; card do dashboard compara % alocado pelo Optimizer vs. yield de protocolo de referência (ADR-0007) |
| **Yield (APY)** | Taxa de rendimento anual de um protocolo DeFi (ex: Aave), consultada via DefiLlama `/yields` — só leitura de dado público, sem execução/depósito real |
| **Slippage heurístico** | Acréscimo de custo estimado por faixa de volume no Rail Comparator, aproximando perda de liquidez em conversões grandes — não é modelo de order book real (ADR-0007, débito técnico #11) |
| **Modo degradado** | Estado explícito de uma simulação em que uma fonte pública indisponível foi substituída por fallback documentado; o cálculo continua, mas a interface identifica a fonte e a premissa usada |
| **Caso de uso** | Segmento do pagamento: `domestico` (BRL→BRL, só PIX) ou `cross_border` (converte BRL↔USD: Wire/USDT/USDC). Comparação de trilhos só é válida dentro do mesmo caso de uso (ADR-0008) |
| **On-ramp / Off-ramp** | Entrada (BRL→stablecoin, prêmio real de mercado) e saída (stablecoin→USD, 0,3% fixo) do trilho cripto — o custo de conversão que o modelo antigo ignorava (ADR-0008) |
| **DCOH (days cash on hand)** | Dias de opex cobertos pelo caixa; base corporativa pra dimensionar reserva (default 60d), no lugar de "meses de despesa" (ADR-0009) |
| **Working capital no trilho** | Stablecoin tratada como capital de giro EM TRÂNSITO no trilho cross-border (≈ fluxo × dias de settlement), não investimento de reserva (ADR-0009) |
| **Cash equivalent** | Caixa e equivalentes (depósito à vista, T-bill ≤90d). Stablecoin NÃO é cash equivalent (US GAAP/IFRS, ASU 2023-08) → excluída da reserva de emergência (ADR-0009) |
| **Cap de política** | Limite de sleeve de ativos digitais aprovável por board (1–5%; default 5%) — um dos tetos sobre a stablecoin (ADR-0009) |
| **Haircut de liquidez** | Desconto aplicado ao valor de liquidez da stablecoin pelo ES do Depeg Engine: `valor × (1 − ES)` (ADR-0009) |
| **Custo de carrego** | O que a reserva de cash deixa de render por estar parada: `valor × (taxa_referência − yield_atual)`. Referência: CDI (BRL) / T-bill (USD) — ambos cash-equivalents, sem risco de DEPEG adicional; a soma dos dois gaps NÃO é "sem risco algum" (ver Diferencial de juros / carry trade, ADR-0012 #7) (ADR-0010) |
| **3º pilar (Capital Markets & Funding)** | O capital dorme na **reserva**, não no giro em stablecoin (que transita em dias). Por isso o custo de oportunidade se mede no cash, não na cripto (ADR-0010 supersede ADR-0007 §B) |
| **Exposição cambial líquida** | `recebimento_usd_30d − pagamento_usd_30d`. A decisão de hedge usa este número, não só "tem recebimento em USD?" — evita recomendar liquidar USD numa empresa que é líquida SHORT dólar (ADR-0012 #6) |
| **Defasagem PTAX×Binance** | Divergência entre a PTAX (BCB, D-1) e o mid do order book (Binance, tempo real). Acima do limiar (1%), o prêmio de on-ramp pode refletir câmbio se movendo no dia, não custo real de liquidez — disclaimer exposto na UI, não "correção" (não existe FX oficial intradiário gratuito) (ADR-0012 #8) |
| **Fronteira de indiferença (Wire)** | Spread de Wire (%) em que o custo do Wire empata com o melhor trilho stablecoin. Abaixo dela, Wire vira mais barato — expõe que a manchete de economia depende do spread negociado, não só do IOF (ADR-0012 #1) |
| **ES estressado (piso)** | Piso aplicado ao ES usado no HAIRCUT de liquidez (não na classificação de risco/teto), igual ao ES real medido no evento USDC-SVB (4,18% horário). Evita que o haircut colapse a zero em regime calmo — ES histórico é procíclico (ADR-0012 #3/#4) |
| **Diferencial de juros / carry trade** | `CDI − T-bill`. Por paridade descoberta de juros, aproxima a depreciação cambial ESPERADA do BRL — o custo de carrego não é "dinheiro grátis" quando esse diferencial é grande (alerta acima de 5pp, ADR-0012 #7) |

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
| 0007 | Opportunity Cost (yield, DefiLlama) + heurística de slippage por volume; hedge real (put option) rejeitado por violar escopo negativo do ADR-0003 | **Partially Superseded** (§B, pelo 0010) |
| 0008 | Modelo de custo honesto do Rail Comparator: spread on/off-ramp no trilho stablecoin + segmentação por caso de uso + religação do filtro eFX (auditoria F1/F2/F7) | Accepted |
| 0009 | Conformidade com tesouraria corporativa: reserva em cash-only (stablecoin não é caixa equivalente), stablecoin como working capital no trilho com teto triplo + haircut ES; âncora de escala Nubank FY2025 | Accepted |
| 0010 | 3º pilar reenquadrado: custo de carrego da **reserva de cash** (BRL vs CDI, USD vs T-bill), não yield de stablecoin (premissa morta pelo 0009). Implementa também o slippage por volume (ponto C do 0007) | Accepted |
| 0011 | Rigor upgrade pós-aula: premissas viram medições onde há dado de mercado gratuito (IOF isento p/ importação de bens, granularidade horária, order book real via Binance, ES ponderado por carteira, âncora trocada p/ Azul); mantém normativo explícito (cap de política) onde fingir medição seria número mágico | Accepted |
| 0012 | Auditoria 2026-07-30: hedge por exposição líquida (não só sinal de recebimento), fallback do ES coerente (teto×haircut), slippage/defasagem por moeda certa, spread do Wire parametrizável + fronteira de indiferença, ES horário medido na janela SVB (4,18%, margem 0,82pp), piso de ES estressado no haircut de liquidez, ressalva de paridade de juros no custo de carrego, TTL nos caches de taxa | Accepted |
| 0013 | Reposiciona o produto para pacote de decisão pré-pagamento; execução financeira, cotação e parecer jurídico ficam fora do escopo | Accepted |
| 0014 | Dashboard modular para portfólio: Depeg Risk Engine primeiro; renderização isolada em `src/views/` | Accepted |
| 0015 | Demo pública atualiza histórico sob demanda, com TTL de 24 h e lock no Postgres | Accepted |

---

## Débitos técnicos conhecidos

1. Spread bancário é estimado por faixa pública (não cotação ao vivo)
2. Faturas B2B são sintéticas (mock), não dados reais de parceiro
3. Sem API REST (só dashboard + módulos Python)
4. BCB 561 implementada como regra determinística (sem interpretação jurídica)
5. ~~Liquidity Optimizer usa heurística fixa (50/30/20) sem base quantitativa~~ **RESOLVIDO** — `src/depeg_risk.py` calcula VaR/ES sobre histórico real (DefiLlama) e classifica risco em faixas calibradas com eventos reais (USDC-SVB, UST); teto de alocação em `src/otimizador.py` deriva desse cálculo, não mais fixo. Ver ADR-0003.
6. ~~Projeto é 100% stateless (sem histórico persistido)~~ **RESOLVIDO** — persistência via SQLAlchemy + Postgres em Docker (ADR-0005); histórico 2022→hoje ingerido, série de risco (backtest) persistida.
7. ~~Depeg Risk Engine mede risco só sobre USDC e aplica o teto ao total em stablecoin~~ **RESOLVIDO** (ADR-0011 #4) — `avaliar_risco_carteira` mede sobre a carteira real (USDC+USDT ponderados via `desvio_carteira`); a correlação emerge do dado (inner join por timestamp). Composição configurável no dashboard.
8. ~~VaR/ES usa granularidade diária, que suaviza o mínimo intra-dia real~~ **RESOLVIDO** (ADR-0011 #2) — risco atual usa série horária (`period=1h`, ~2160 pts em 90d, cauda de ~65 e captura o mínimo real 0,8767 de mar/2023). Backtest histórico segue diário (trend de anos).
9. `var_es_historico` aceita `confianca` fora de [0,1] (ex: 1.5, -0.1) silenciosamente, sem validar — clampa pro mesmo resultado do limite válido. Baixo risco (função interna, nunca exposta a input de usuário), mas sem guarda explícita. Achado no PAVC audit 2026-07-05.
10. `_utc_naive`/`_com_utc` (`src/repositorio.py`) assumem implicitamente que `datetime` sem timezone já está em UTC, sem validar. Se código futuro passar naive em horário local, persiste silenciosamente errado. Achado no PAVC audit 2026-07-05.
11. Heurística de slippage por volume (`comparador.py`, ADR-0007) é aproximação documentada — não modela order book/liquidez real, aplica acréscimo estimado por faixa de valor, mesmo padrão do débito #1 (spread bancário estimado). Não usar como cotação precisa.
12. ~~Custo do trilho stablecoin = só gas (ignora on/off-ramp); PIX domina comparação apples-to-oranges~~ **RESOLVIDO** (ADR-0008) — custo stablecoin = spread on-ramp (prêmio real) + gas + off-ramp (0,3% fixo); comparador segmenta por caso de uso (doméstico/cross-border) e religa o filtro eFX (BCB 561).
13. ~~Otimizador com duas lógicas de alocação inconsistentes; reserva "3 meses" e alvo 50–60% stablecoin fora de conformidade corporativa~~ **RESOLVIDO** (ADR-0009) — alocação única: reserva em cash-only por DCOH, stablecoin como working capital com teto triplo (necessidade/política 5%/depeg) + haircut ES.
14. Off-ramp stablecoin (0,3%, `comparador.py`) é constante conservadora estimada, não medida (ADR-0008). Mesmo status do débito #1.
15. `DIAS_SETTLEMENT` (5) e `CAP_POLITICA_STABLECOIN` (5%) em `otimizador.py` são premissas de política, não medidas (ADR-0009). Configuráveis, documentadas.
16. ES de robustez rasa: janela 90d @ 97% = cauda de 3 amostras diárias (`tamanho_cauda`), estimador sensível a outlier. **Parcialmente mitigado** (ADR-0012 #2) — medido ao vivo, o ES(97%) horário da mesma janela SVB é 4,18% (cauda de ~65 horas), ainda "baixo" mas com margem de só 0,82pp até o corte de 5% (era 3,24pp no diário). **Continua aberto**: as ~65 horas da cauda horária não são ~65 eventos independentes — são a mesma crise de poucos dias re-amostrada em granularidade fina (autocorrelação), então o n efetivo de eventos segue perto de 1-3, não 65. O piso de ES estressado (débito resolvido, ADR-0012 #3/#4) mitiga a CONSEQUÊNCIA (haircut colapsando a zero em calmaria), não a causa (amostra pequena de eventos de cauda independentes).
17. Perfil de referência (`perfil_referencia.py`) mistura dado real de escala (Azul S.A. FY2024, 20-F, com fonte) e premissa de fluxo cross-border (ilustrativa). Cada campo rotulado. Âncora trocada de Nubank (banco) para Azul (aérea com passivo em USD — caso clássico de tesouraria cambial), ADR-0011 #5.
18. `yield_atual` do caixa (default 0%, `custo_carrego.py`) — **relabelado** (ADR-0012 #7) como cenário PIOR CASO explícito na UI, não estimativa realista; tesourarias grandes já remuneram parte do caixa via sweep/fundo DI. Input configurável no dashboard (ADR-0010).
19. Custo de **float do trilho** (capital preso durante os dias de settlement, rendendo 0%) não é modelado — é pequeno e tende a se cancelar entre trilhos (Wire também é T+2/T+5). Decisão consciente do ADR-0010.
20. Slippage por volume (`FAIXAS_SLIPPAGE`, `comparador.py`) é acréscimo por faixa, **não** modelo de order book real (ADR-0010, ponto C do 0007). Herda o status do débito #11.
21. ~~Custo do trilho stablecoin ignora sensibilidade ao spread do Wire; PIX vs Wire vs stablecoin usava constante fixa de 2,5%~~ **RESOLVIDO** (ADR-0012 #1) — `spread_wire_percent` é parâmetro configurável; `spread_indiferenca_wire` calcula a fronteira em que a conclusão inverte. **Débito remanescente**: assume que o spread negociável não depende do valor da fatura (tickets maiores tipicamente negociam melhor spread — não modelado).
22. ~~Hedge cambial decidido só por `recebimento_usd > 0`, ignorando o passivo~~ **RESOLVIDO** (ADR-0012 #6) — decisão de hedge usa `exposicao_liquida_usd_30d = recebimento - pagamento`; mantém/reforça USD sempre que a exposição líquida é != 0, nos dois sentidos (long ou short).
23. `ES_STRESSED_FLOOR_SVB` (0,0418, `depeg_risk.py`, ADR-0012 #3/#4) é ancorado em **1 evento histórico** (mesmo problema de amostra pequena do débito #16 e do ADR-0004 §2.5) — é o melhor dado disponível hoje, não uma calibração robusta. Mais eventos de depeg reais refinariam o piso.
24. `caso_uso="domestico"` só tem PIX elegível — falta TED como segundo trilho doméstico pra comparação real (a aba mostra 1 linha, economia sempre R$0). Não implementado por falta de dado de custo de TED com fonte pública (evitar novo número mágico); UI avisa explicitamente da limitação.
25. Prêmio de on-ramp (`premio_onramp`, `comparador.py`) compara preço CoinGecko (tempo real) com PTAX (BCB, D-1) — defasagem de fonte que pode dominar o número em dia de câmbio volátil. **Mitigado com disclaimer** (ADR-0012 #8, `defasagem_ptax_binance_pct` + aviso na UI), não corrigido — não existe FX oficial intradiário gratuito pra eliminar de vez.
26. Custo de carrego (`custo_carrego.py`) soma gap em BRL (CDI) e gap em USD (T-bill) — matematicamente correto, mas o diferencial CDI−T-bill aproxima, por paridade descoberta de juros, a depreciação cambial ESPERADA do BRL. **Mitigado com disclaimer** (ADR-0012 #7, `diferencial_juros_cdi_tbill_pct` + `alerta_carry_trade`), não corrigido — é característica do mercado, não erro de cálculo.

## Escopo negativo (ADR-0003)

- Sem autenticação/multi-tenant (single-tenant, demo de portfolio)
- Sem execução real de transação (nunca integra custodian/exchange real)
- Sem assessoria jurídica ou fiscal real (compliance filter é interpretação própria, com disclaimer)
- Sem apuração de IR/renda (só IOF)
- Uma tesouraria simulada por vez

## Pontos de melhoria conhecidos, fora de escopo (ADR-0007)

- **Hedge real (put option DeFi)**: sugerido por revisão externa como extensão do Depeg Risk Engine (medir risco → executar hedge, não só reduzir alocação). Rejeitado: exige custódia/execução real de transação, violando escopo negativo do ADR-0003. Uma versão "fake" (rótulo sem lastro) foi descartada por não agregar informação além do que o Optimizer já comunica.
