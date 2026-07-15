# Glossário — StableTreasury

> Todos os termos usados no projeto, agrupados por domínio. Onde importa, a coluna **por que importa** explica a decisão por trás do conceito. Para a Linguagem Ubíqua canônica (fonte de verdade dos termos de código), ver `AGENTS.md`.

---

## 1. Risco quantitativo

| Termo | Significado | Por que importa |
|-------|-------------|-----------------|
| **VaR (Value at Risk)** | Perda no **limiar** da pior fatia de cenários, a dado nível de confiança. Ex: VaR(97%) = perda no corte dos 3% piores dias. | É uma fronteira, não uma média — tem um ponto cego: não diz **quão fundo** a cauda vai. |
| **Expected Shortfall (ES)** | Perda **média dentro** da cauda (além do VaR). Sempre ES ≥ VaR. | Basel III/FRTB abandonou o VaR e adotou o ES 97,5% justamente por causa da cegueira de cauda que quebrou bancos em 2008. É o teto de alocação **e** o haircut de liquidez do projeto. |
| **Desvio do peg** | Distância do preço à paridade: `preço − 1,00`. A métrica de risco do projeto (não retorno diário). | Um depeg gradual (US$1,00→0,90 em muitos passos) tem retorno diário ~0 e passaria despercebido; o desvio revela o buraco a qualquer instante. Por ser um **nível** (não retorno), não há regra do √t — misturar granularidade diária/horária é livre. |
| **Simulação histórica** | Cálculo de VaR/ES sobre a distribuição empírica real dos dados, sem assumir normalidade. | Cripto tem cauda gorda; assumir distribuição normal (VaR paramétrico) subestimaria o risco de cauda — o erro de 2008. |
| **Cauda (tail)** | O conjunto dos piores casos que formam o ES. Tamanho = `round((1−confiança) × nº amostras)`. | 90 dias diário @ 97% = só 3 amostras (frágil); 90 dias **horário** = ~65 (robusto). Motivo do upgrade de granularidade (ADR-0011). |
| **Confiança** | Nível do VaR/ES (ex: 97%). Quanto maior, mais extrema a cauda observada. | 97% alinha o modelo ao padrão regulatório bancário (Basel FRTB, ES 97,5%). |
| **Backtest** | Reconstrução do risco ao longo do tempo com **janela deslizante** — "o que o modelo teria dito em cada momento". | É o que faz o spike do SVB (mar/2023) aparecer sozinho no gráfico, sem hardcode. Prova de que o motor funciona. |
| **Janela deslizante** | Janela móvel de N dias que avança no tempo, recalculando o risco a cada passo. | Explica por que o ES fica "travado" por ~40 dias após o SVB: os piores dias permanecem na janela de 90d até expirarem. O ES é uma memória de 90 dias. |
| **Haircut de liquidez** | Desconto no valor de liquidez de um ativo de risco: `valor × (1 − ES)`. | Reusa o ES do Depeg Engine para expressar quanto de uma posição em stablecoin "vale" como liquidez real, dado o risco. |
| **Basel III / FRTB** | Marco regulatório de risco de mercado dos bancos (Fundamental Review of the Trading Book). | Origem da escolha ES 97,5% — "meço risco como um banco mede, não como um tutorial mede". |

---

## 2. Stablecoin & cripto

| Termo | Significado | Por que importa |
|-------|-------------|-----------------|
| **Stablecoin** | Cripto atrelada a uma moeda fiduciária (USDT, USDC ao USD). | O ativo central do trilho barato — e o objeto do risco de depeg. |
| **Peg** | A paridade-alvo (1 stablecoin = US$ 1,00). | O ponto de referência de todo o cálculo de risco. |
| **Depeg** | Desvio da stablecoin em relação ao peg. | O evento que o motor mede. Ex: USDC caiu a ~0,88 no SVB (mar/2023). |
| **On-ramp** | Entrada no trilho cripto: comprar stablecoin com BRL (paga prêmio de mercado). | Custo real do trilho que o modelo antigo ignorava (tratava como "só gas"). |
| **Off-ramp** | Saída do trilho: vender stablecoin por USD/BRL no destino. | A outra perna do custo de conversão (0,3% no modelo, constante conservadora). |
| **Gas fee** | Taxa de rede blockchain para uma transação on-chain (gwei × gas units × preço do token nativo). | Componente do custo do trilho stablecoin; varia com congestionamento da rede. |
| **Order book** | Livro de ofertas (bids/asks) de uma exchange, com preço e quantidade por nível. | Fonte do slippage **medido** (Binance USDT/BRL), substituindo a estimativa por faixa. |
| **VWAP (Volume-Weighted Average Price)** | Preço médio de execução ao "caminhar" o order book nível a nível para um dado volume. | Transforma slippage de premissa em medição de microestrutura de mercado real. |
| **Slippage** | Custo extra de mover um volume grande: `(VWAP − mid) / mid`. | Volume grande "anda" o book e encarece a conversão. Medido no book real (ADR-0011). |
| **Proof-of-Reserve** | Prova on-chain/atestada de que o emissor tem reservas equivalentes ao supply. | Sinal de solidez do lastro — relevante para diferenciar risco entre emissores. |
| **Attestation** | Relatório público (Circle/Tether) que declara a composição das reservas. | Cadência trimestral — motivo da janela de risco de 90 dias. |
| **DefiLlama** | Agregador de dados on-chain (grátis). Fonte do histórico de preço de peg (2022→hoje). | Cobre os eventos de stress reais (UST 2022, SVB 2023) que a CoinGecko free (365d) não alcança. |

---

## 3. Trilhos & pagamento

| Termo | Significado | Por que importa |
|-------|-------------|-----------------|
| **Trilho (Rail)** | Canal de pagamento: PIX, Wire/SWIFT, USDT, USDC. | A escolha que o Rail Comparator otimiza. |
| **Rail Comparator** | Módulo que compara o custo total de cada trilho para uma fatura. | Pilar Cash Management. |
| **Wire / SWIFT** | Transferência bancária internacional tradicional (spread FX + IOF + tarifa). | O trilho "caro e regulado" — a base de comparação. |
| **PIX** | Pagamento instantâneo doméstico brasileiro (custo zero). | Só serve caso de uso **doméstico** — não disputa cross-border (correção do bug F2). |
| **Spread FX** | Diferença entre a taxa comercial de câmbio e a praticada pelo banco. | Componente dominante do custo do Wire (~2,5%). |
| **Caso de uso** | Segmento do pagamento: `domestico` (BRL→BRL) ou `cross_border` (converte BRL↔USD). | Comparar trilhos só é válido dentro do mesmo caso de uso — senão é apples-to-oranges. |
| **Cross-border** | Pagamento que cruza fronteira e exige conversão de moeda. | Onde a escolha de trilho de fato importa; onde a arbitragem do stablecoin existe. |

---

## 4. Tesouraria corporativa

| Termo | Significado | Por que importa |
|-------|-------------|-----------------|
| **Tesouraria** | Área que gere o caixa, a liquidez, o risco cambial e o funding de uma empresa. | O "cliente" do projeto. |
| **Cash equivalent** | Caixa e equivalentes: depósito à vista, money market, T-bill ≤90d. | **Stablecoin NÃO é cash equivalent** (US GAAP/IFRS, ASU 2023-08) → não pode compor a reserva. Decisão que reescreveu o otimizador. |
| **Reserva** | Buffer de liquidez para obrigações e emergências, mantido em **cash**. | Dimensionado por DCOH; stablecoin fica de fora. |
| **DCOH (days cash on hand)** | Dias de opex que o caixa cobre. Base corporativa para dimensionar a reserva. | Substitui a heurística de "meses de despesa" (que é regra de runway de startup, não de empresa grande). |
| **Working capital (no trilho)** | Capital de giro **em trânsito** no trilho cross-border (≈ fluxo × dias de settlement). | O papel correto da stablecoin: giro operacional, não investimento de reserva. Resultado: ~4% do caixa, não 50-60%. |
| **Tier (1/2/3)** | Camadas de caixa: operacional / reserva-core / estratégico. | Estrutura clássica de tesouraria corporativa que o modelo segue. |
| **RCF (revolving credit facility)** | Linha de crédito rotativa comprometida — o backstop de liquidez real. | A liquidez de emergência real de uma empresa grande não é caixa parado, é a RCF. (Fora do escopo do modelo, mencionada.) |
| **Custo de carrego (carry cost)** | O que a reserva parada deixa de render vs. a referência: `valor × (taxa − yield_atual)`. | O 3º pilar (Capital Markets & Funding): o capital dorme na reserva, não no giro. |
| **Opportunity cost** | Custo de oportunidade — o retorno abrido mão por uma escolha de alocação. | Base do 3º pilar; medido no cash (CDI/T-bill), não na stablecoin. |
| **Cap de política** | Limite de sleeve de ativo digital aprovável por board (1–5%; default 5%). | Um dos tetos sobre a stablecoin. **Premissa normativa** — deliberadamente não virou "medição" (seria número mágico). |
| **Hedge natural** | Manter USD quando se tem receita/obrigações em USD, casando ativo e passivo. | Por que a aérea (Azul) mantém ~43% em USD na alocação — casa com o passivo em dólar. |
| **Cash Management / Risk / Capital Markets & Funding** | Os 3 pilares clássicos de tesouraria. | O projeto cobre os três: Rail Comparator, Depeg Engine, Custo de Carrego. |

---

## 5. Regulatório & macro (Brasil + contábil)

| Termo | Significado | Por que importa |
|-------|-------------|-----------------|
| **IOF** | Imposto sobre Operações Financeiras — incide no câmbio, por decreto. | Importação de bens é **isenta** (Art. 15-B); serviços/remessa a terceiros = 3,5%. A arbitragem do stablecoin é máxima onde o IOF é alto. |
| **eFX** | Electronic Foreign Exchange — câmbio eletrônico regulado. | Onde a BCB 561 proíbe stablecoin como trilho de liquidação. |
| **BCB 519 / 520 / 521 / 561** | Resoluções do Banco Central: ativos virtuais / KYC / segregação patrimonial / proibição em eFX (out/2026). | O Compliance Filter as codifica; a 561 é o **prazo de validade** da arbitragem. |
| **e-DRS** | Sistema de declaração ao BCB para operações acima de R$ 500k (Res. 521). | Gatilho de aviso no Compliance Filter. |
| **KYC (Know Your Customer)** | Identificação obrigatória do cliente (Res. 520). | Aviso do Compliance Filter em operações com ativo virtual. |
| **PTAX** | Taxa de câmbio de referência USD/BRL do Banco Central (série SGS 10813). | Base do cálculo de custo dos trilhos e da conversão. |
| **CDI** | Taxa interbancária brasileira (~14,15% a.a., série SGS 4389). | Referência de rendimento de cash-equivalent em BRL (custo de carrego). |
| **Selic** | Taxa básica de juros do Brasil (meta, série SGS 432). | Referência macro; próxima do CDI. |
| **T-bill** | Título do Tesouro americano de curto prazo (~3,7% a.a., US Treasury). | Referência de rendimento de cash-equivalent em USD. |
| **ASU 2023-08** | Norma do FASB: cripto mensurada a valor justo, **fora** de caixa & equivalentes. | Base contábil de "stablecoin não é cash equivalent" → exclusão da reserva. |
| **LGPD** | Lei Geral de Proteção de Dados (Brasil). | Regra de engenharia da base: anonimizar PII. |

---

## 6. Infraestrutura & engenharia

| Termo | Significado | Por que importa |
|-------|-------------|-----------------|
| **ADR (Architecture Decision Record)** | Registro versionado de uma decisão arquitetural (o quê, por quê, alternativas). | O projeto tem 11 (0001–0011) — a trilha de raciocínio, incluindo decisões rejeitadas/superseded. |
| **Backfill** | Carga inicial do histórico no banco (2022→hoje), paginada. | Popula `peg_prices` para o backtest. Rodada via `scripts/seed_db.py`. |
| **Idempotência** | Rodar de novo não duplica: insere só o que falta. | `salvar_precos` lê os timestamps existentes e insere só os novos, sem `ON CONFLICT` (portável SQLite/Postgres). |
| **Fallback** | Valor de contingência quando uma API falha (loga warning, não quebra). | O projeto prefere degradar com número estimado a derrubar o dashboard. |
| **Dev/prod parity** | Mesmo motor de banco (Postgres) local e em produção. | Evita o clássico "passa no teste (SQLite), quebra em prod (Postgres)". |
| **Neon** | Postgres gerenciado na nuvem (free tier). Alvo do deploy. | Mantém dev/prod parity em produção sem custo. |
| **Cold start (Neon)** | Free tier pausa o banco após inatividade; a 1ª consulta demora a "acordar". | Latência esperada no deploy público. |
| **DATABASE_URL** | Variável de ambiente que aponta pro banco (Docker local ou Neon). | Trocar só ela muda o ambiente — o código não muda. |
| **Risk Snapshot** | Registro de risco (ES/VaR/faixa/teto) num momento; a série alimenta o gráfico. | Dado **derivado** (recalculável), separado do preço bruto imutável. |

---

*Fonte de verdade dos termos de código: `AGENTS.md` (Linguagem Ubíqua). Este glossário é a visão didática consolidada.*
