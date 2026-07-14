# StableTreasury — Aula Técnica Completa (ponta a ponta)

> **Objetivo deste documento**: entender o sistema a fundo — a matemática, a engenharia e **por que cada decisão foi tomada** (incluindo as que foram rejeitadas e as que morreram no caminho).
> **Data**: 2026-07-14 · **Estado**: 62 testes passando · ADRs 0001–0010
> **Como ler**: as seções 1–3 são o sistema. A seção 4 é a trilha de decisões. A 5 é a auditoria (onde o projeto estava errado). A 6 é a parte de finanças corporativas — a mais importante para defender o projeto.

---

## 1. O problema de negócio

Uma tesouraria de fintech brasileira que opera cross-border precisa responder **quatro perguntas**, todo dia:

| #   | Pergunta                                | Módulo que responde             |
| --- | --------------------------------------- | ------------------------------- |
| 1   | Qual trilho de pagamento custa menos?   | **Rail Comparator**             |
| 2   | Isso é legal?                           | **Compliance Filter**           |
| 3   | Posso confiar em stablecoin agora?      | **Depeg Risk Engine**           |
| 4   | Como alocar o caixa?                    | **Liquidity Optimizer**         |
| 5   | O caixa parado está me custando quanto? | **Custo de Carrego** (3º pilar) |

O valor do sistema **não** é "usar cripto". É medir, com rigor, uma **arbitragem regulatória com prazo de validade**: hoje o trilho stablecoin dribla o IOF de câmbio; a **Resolução BCB 561 fecha essa janela em out/2026**. O projeto mede a janela, o risco de usá-la, e o custo de não usá-la.

---

## 2. Arquitetura — o fio de dados

```
            ┌──────────────────────────────────────────────┐
            │  coletor_precos.py  (ÚNICA porta de rede)    │
            │  CoinGecko · Etherscan · BCB SGS · Treasury  │
            └───────────┬──────────────────────────────────┘
                        │ (todo I/O externo passa aqui; nada mais faz requests)
        ┌───────────────┼────────────────┬──────────────────┐
        ▼               ▼                ▼                  ▼
  comparador.py   depeg_risk.py    otimizador.py     custo_carrego.py
  (custo/trilho)  (VaR/ES)         (alocação)           (3º pilar)
        │               │                ▲                  ▲
        │               │                │                  │
        ▼               ▼                │                  │
  compliance.py   ingestao.py ──► repositorio.py ──► db.py  │
  (BCB 561)       (backfill+       (persistência)   (schema)│
                   backtest)                                │
        └───────────────┴────────────────┴──────────────────┘
                        ▼
                     app.py  (Streamlit — só orquestra e exibe)
```

**Princípio de design nº 1 — isolamento de I/O.** Nenhum módulo além de `coletor_precos.py` faz `requests.get`. Isso: (a) torna todo o resto testável sem rede; (b) centraliza a política de degradação; (c) permite trocar fonte de dado sem tocar na lógica.

**Princípio nº 2 — o único acoplamento matemático real** é `depeg_risk → otimizador`: o ES (Expected Shortfall) vira **teto de alocação** e **haircut de liquidez**. Rail Comparator e Compliance são paralelos e independentes; só convergem na decisão final do humano.

---

## 3. Camada por camada (técnica profunda)

### 3.1 `coletor_precos.py` — coleta e degradação

Toda função segue o mesmo padrão:

```python
def preco_stablecoin(moeda="usdt"):
    try:
        resp = requests.get(COINGECKO_URL, params={...}, timeout=10)
        resp.raise_for_status()          # 4xx/5xx viram exceção
        return resp.json().get(ids, {}).get("brl")
    except Exception as e:
        logger.warning(f"Falha ...: {e}")  # loga, não estoura
        return None                        # "não sei" — quem chama decide
```

**Decisão:** o coletor **nunca inventa o número de fallback**. Ele devolve `None` = "não consegui". Quem decide o valor de substituição é o módulo consumidor, que conhece o significado de negócio do dado.

**Onde isso quase deu errado (achado F5 da auditoria):** `comparador.py` usava `ptax_venda() or 5.0` e `otimizador.py` usava `or 5.7` — **14% de divergência** no mesmo câmbio, no mesmo instante. Corrigido: constante única `PTAX_FALLBACK = 5.7` exportada pelo coletor.

**Fontes de dado (todas grátis, sem API key exceto gas):**

| Dado                      | Fonte                      | Observação                                      |
| ------------------------- | -------------------------- | ----------------------------------------------- |
| Preço USDT/USDC/ETH/MATIC | CoinGecko                  | sem key                                         |
| Gas fee                   | Etherscan / PolygonScan    | **exige key**; sem key → faixa fixa (achado F6) |
| PTAX (câmbio)             | BCB SGS série 10813        | sem key                                         |
| **CDI**                   | BCB SGS série **4389**     | sem key — 14,15% a.a.                           |
| **T-bill**                | US Treasury `fiscaldata`   | sem key — 3,706% a.a.                           |
| Histórico de peg          | DefiLlama `coins.llama.fi` | sem key, cobre 2022→hoje                        |

**Armadilha do `@lru_cache(maxsize=1)`** em `ptax_venda`, `taxa_cdi`, `taxa_tbill`: cacheia pela vida do processo. Em demo (Streamlit recarrega) é bom — evita rate-limit. Em produção 24/7, a taxa **nunca atualizaria**. Simplificação consciente.

---

### 3.2 `iof_tabela.py` — dado regulatório fora do código

IOF muda **por decreto federal**, não por deploy. Por isso mora em `data/raw/iof_aliquotas.yaml`, carregado uma vez e cacheado em módulo. Regra do projeto: *"IOF como parâmetro, não hardcoded"*.

---

### 3.3 `comparador.py` — Rail Comparator (aqui moravam os 2 piores bugs)

#### A matemática do custo, por trilho

**Wire (SWIFT):**
```
spread  = valor_usd × 2,5% × ptax     # spread FX do banco
iof     = valor_usd × alíquota × ptax # imposto (3,5% em remessa)
tarifa  = US$25 × ptax                # tarifa fixa
custo   = spread + iof + tarifa
```
Detalhe elegante: como `valor_usd = valor_brl / ptax`, a PTAX **se cancela** em `spread` e `iof` — o custo em BRL independe do câmbio usado. Por isso o teste `test_iof_35_para_remessa` é robusto mesmo com PTAX ao vivo.

**Stablecoin — o custo REAL (jornada de 3 pernas):**

O modelo original dizia que o trilho stablecoin custava **só gas**. Isso é ficção: uma tesouraria não "tem USDT", ela tem BRL.

```
BRL ──(1) compra USDT──► USDT ──(2) transfere──► USDT ──(3) vende──► USD
     prêmio on-ramp             gas                    spread off-ramp
     + slippage por volume      (o único modelado antes)
```

```python
premio_onramp = max(0, preco_usdt_brl / ptax - 1)   # prêmio REAL de mercado
slippage      = slippage_por_volume(valor_brl)       # faixas: 0% → 0,5%
spread_onramp = valor_brl × (premio_onramp + slippage)
spread_offramp= valor_brl × 0,3%                     # constante conservadora
gas_brl       = avg_gwei × 1e-9 × 65_000 × preco_eth_usd × ptax
custo         = spread_onramp + gas_brl + spread_offramp
```

- `1e-9`: converte gwei → ETH (1 gwei = 10⁻⁹ ETH).
- `65_000` gas units: transferência de token ERC-20 (não os 21.000 de ETH nativo — token executa contrato).
- `max(0, ...)`: se o USDT estiver **abaixo** da PTAX, o prêmio é 0, não negativo (não é "lucro").

#### Slippage por volume (aproximação documentada)

```python
FAIXAS_SLIPPAGE = [
    (100_000,    0.0),   # até R$100k: sem atrito relevante
    (1_000_000,  0.1),   # 0,1%
    (10_000_000, 0.25),  # 0,25%
    (inf,        0.5),   # 0,5%
]
```
**É honesto sobre o que não é:** não modela order book real (não há fonte gratuita de profundidade). É acréscimo por faixa — mesmo padrão do spread bancário. Teste garante **monotonicidade**: converter mais nunca sofre proporcionalmente *menos* atrito.

#### Segmentação por caso de uso (o bug conceitual mais grave)

Antes: PIX tinha custo `0` fixo e **vencia toda comparação**, sempre. Mas **PIX é doméstico** — não faz pagamento internacional. Comparar PIX com Wire é comparar coisas que servem casos de uso diferentes.

```python
_TRILHOS_DOMESTICO    = ("PIX",)
_TRILHOS_CROSS_BORDER = ("Wire (SWIFT)", "USDT (ERC-20)", "USDT (Polygon)",
                         "USDC (ERC-20)", "USDC (Polygon)")
```
Mais: se `eletronico_cambio=True`, aplica-se `filtrar_trilhos_permitidos` (BCB 561) e as stablecoins **saem da comparação** — a função que estava testada mas **desligada do produto**.

#### O número honesto

| Trilho (cross-border, R$50k) | Custo        | %                                           |
| ---------------------------- | ------------ | ------------------------------------------- |
| USDT (Polygon)               | R$ 150       | 0,30%                                       |
| USDC (Polygon)               | R$ 300       | 0,60%                                       |
| **Wire (SWIFT)**             | **R$ 3.128** | **6,26%** (spread 2,5% + IOF 3,5% + tarifa) |

Economia real ≈ **90%**, não "99,99%". E a economia existe porque o stablecoin **dribla o IOF** — a arbitragem que a BCB 561 encerra.

---

### 3.4 `compliance.py` — Compliance Filter

Não é matemática, é **motor de regra determinística** mapeado 1:1 ao texto das resoluções:

| Regra                                                        | Efeito              | Severidade            |
| ------------------------------------------------------------ | ------------------- | --------------------- |
| **BCB 561** — stablecoin proibida em eFX (vigência out/2026) | `permitido = False` | 🔴 **erro** (bloqueia) |
| **BCB 520** — KYC obrigatório em ativo virtual               | aviso               | 🟡 aviso               |
| **BCB 521** — valor > R$500k exige declaração e-DRS          | aviso               | 🟡 aviso               |

**A assimetria importa:** erro **bloqueia** a operação; aviso apenas informa. Nem toda exigência regulatória impede a transação — algumas só a invalidam sem uma providência adicional. Modelar isso como um booleano único perderia o sinal.

---

### 3.5 `depeg_risk.py` — o núcleo quantitativo

#### (a) A métrica certa: **desvio do peg**, não retorno diário

```python
def desvio_peg(precos):
    return np.array(precos) - 1.0
```

Por que **não** usar retorno diário (`(p_t − p_{t−1})/p_{t−1}`), que é o padrão em risco de ações/FX?

> Uma stablecoin que cai de US$1,00 → US$0,90 em **30 passos pequenos** tem retorno diário baixíssimo em cada passo — o modelo de retorno **não veria o depeg**. Mas o desvio acumulado (`preço − 1,00`) revela o buraco a qualquer momento.

Isso é escolha de métrica **alinhada ao fenômeno**, não cópia de padrão de outro domínio.

#### (b) VaR e Expected Shortfall por **simulação histórica**

```python
def var_es_historico(retornos, confianca=0.99):
    perdas = -retornos                        # depeg = perda; inverte sinal
    perdas_ordenadas = np.sort(perdas)[::-1]  # pior perda primeiro
    n = len(perdas_ordenadas)
    tail_count = tamanho_cauda(n, confianca)  # quantos casos formam a cauda
    var = perdas_ordenadas[tail_count - 1]    # LIMIAR da cauda
    es  = perdas_ordenadas[:tail_count].mean()# MÉDIA dentro da cauda
    return var, es
```

- **Simulação histórica (não paramétrica):** usa a distribuição empírica real. Não assume normalidade — e isso é vital, porque cripto tem **cauda gorda**. VaR paramétrico (normal) subestimaria o risco de cauda sistematicamente. *(Foi exatamente o erro que quebrou bancos em 2008.)*
- **VaR(97%)** = "na pior fatia de 3% dos dias, a perda **mínima** é X" — é um **limiar**.
- **ES(97%)** = "dado que estou nesse pior 3%, a perda **média** ali dentro é Y" — sempre **ES ≥ VaR**.
- **Por que ES e não VaR** vira o teto? VaR não diz **nada** sobre o tamanho do desastre além do corte. ES sim. Basel III/FRTB migrou de VaR 99% para **ES 97,5%** exatamente por essa cegueira de cauda.

#### (c) O bug de ponto flutuante que quase passou

```python
tail_count = max(1, round((1 - confianca) * n))
```
`int()` em vez de `round()` seria um bug silencioso: `(1 - 0.9) * 10` em ponto flutuante dá `0.9999999999999998`, e `int()` **trunca para 0** — perderia a cauda inteira. `max(1, ...)` garante ao menos 1 observação. Bug clássico, invisível, só aparece com confiança alta e amostra pequena.

#### (d) Calibração: os números não são chutes

```python
FAIXAS_RISCO = [
    ("baixo", 0.05, 0.60),   # ES < 5%   → teto 60%
    ("medio", 0.30, 0.30),   # ES < 30%  → teto 30%
    ("alto",  inf,  0.10),   # ES ≥ 30%  → teto 10%
]
```
Ancorados em **ES real de dois eventos**:
- **USDC / colapso do SVB (mar/2023)** — recuperável, voltou ao peg em dias → **ES = 1,76%** → cai em "baixo".
- **UST / Terra (mai/2022)** — catastrófico, nunca recuperou → **ES = 99,32%** → cai em "alto".

**Honestidade (achado F8):** a faixa "médio" (5%–30%) **não contém nenhum evento histórico observado**. É interpolação de bom senso entre um caso recuperável e um catastrófico. É *buffer*, não calibração. Documentado no ADR-0004.

**Por que faixas discretas e não fórmula contínua?** Alocação de capital precisa ser **auditável por comitê**. "Está na faixa de risco médio" é defensável numa mesa de compliance. "A fórmula deu 31,4%" não é. Espelha o rating de crédito (AAA/BB/CCC).

#### (e) Parâmetros: 90 dias, 97%

- **90 dias** = 1 trimestre. Casa com a cadência de *attestation* dos emissores (Circle/Tether publicam trimestralmente) e preserva o **regime atual** (janela longa dilui o risco de hoje com calmaria antiga).
- **97%** = alinhado a **Basel III/FRTB** (ES 97,5%). Storytelling: *"meço risco como um banco mede, não como um tutorial mede."*

#### (f) A fragilidade que assumimos (achado F4)

```python
tamanho_cauda(90, 0.97) == 3
```
Com janela de 90 dias e confiança 97%, o ES é a média de **apenas 3 dias**. Cauda rasa → estimador **ruidoso e sensível a um único outlier**. A matemática está certa; a **robustez** é fraca. Exposto como disclaimer na UI — não escondido. Combina com o débito #8 (granularidade diária suaviza o mínimo intra-dia: USDC tocou **0,8767** hourly em mar/2023, mas a série diária registra ~0,96 — o risco de cauda real é **subestimado**).

---

### 3.6 `db.py` + `repositorio.py` — persistência

**Schema único (SQLAlchemy `MetaData`)** gera tabela idêntica em SQLite (testes) e Postgres (dev/prod). Duas tabelas, com uma separação conceitual importante:

| Tabela           | Natureza                   | Por quê                                                                              |
| ---------------- | -------------------------- | ------------------------------------------------------------------------------------ |
| `peg_prices`     | **bruto, imutável**        | PK composta `(coingecko_id, ts)` impede dois preços do mesmo ativo no mesmo instante |
| `risk_snapshots` | **derivado, recalculável** | se o modelo VaR/ES mudar, re-roda o backtest sobre o bruto sem perder histórico real |

**Dois problemas de engenharia resolvidos aqui:**

1. **Timezone entre dialetos.** SQLite não guarda timezone; Postgres guarda. Sem normalizar, o mesmo código se comporta diferente nos dois — o clássico *"passa no teste (SQLite), quebra em prod (Postgres)"*. Solução: grava sempre naive-UTC (`_utc_naive`), lê sempre recolocando UTC (`_com_utc`).

2. **Idempotência sem `ON CONFLICT`.** Em vez de usar upsert específico de dialeto, lê os `ts` existentes, filtra os novos em Python e insere só esses — com `begin_nested()` (savepoint) **por linha**:

```python
try:
    with conn.begin_nested():      # savepoint
        conn.execute(peg_prices.insert(), [linha])
    inseridos += 1
except IntegrityError:
    pass   # outro processo inseriu esse (id, ts) entre o SELECT e o INSERT (TOCTOU)
           # só ESSA linha aborta; a transação externa sobrevive
```
Mais lento que upsert nativo, mas **portável** entre os dois bancos sem duplicar lógica.

---

### 3.7 `ingestao.py` — backfill e backtest

**Backfill:** DefiLlama rejeita `span` grande, então `janelas_paginacao` quebra 2022→hoje em blocos de 450 dias. Função **pura** (sem rede) → testável sem mockar HTTP. `time.sleep(0.3)` é cortesia com API pública gratuita.

**Backtest (o que faz o gráfico brilhar):**
```python
for fim in range(janela_dias, n + 1, passo_dias):   # janela deslizante
    desvios = desvio_peg(precos[fim-90 : fim])
    var, es = var_es_historico(desvios, confianca=0.97)
    faixa, teto = classificar_risco_e_teto(es)
    salvar_risk_snapshot(...)                        # persiste o snapshot
```
Reconstrói **o que o modelo teria dito em cada semana desde 2022**. É por isso que o **pico de ES em mar/2023 (SVB) aparece sozinho** — sem nenhum hardcode de data. O modelo *descobre* a crise porque o preço real caiu naquela janela. **Isso é a prova de que o modelo funciona.**

---

### 3.8 `otimizador.py` — Liquidity Optimizer (reescrito para conformidade corporativa)

Esta é a camada que **mais mudou**, e a mudança é a lição mais valiosa do projeto. Ver seção 6.

```python
# 1. Reserva operacional em CASH (BRL), por DCOH
reserva_necessaria = gasto_30d × (dcoh_dias / 30)      # default 60 dias
reserva_frac       = min(1, reserva_necessaria / total)

# 2. Stablecoin = working capital EM TRÂNSITO no trilho
giro_necessario = fluxo_pagamento_cross_border × (dias_settlement / 30)  # 5 dias

# 3. TETO TRIPLO (o menor manda)
stablecoin_frac = min(
    need_frac,                # só o giro que de fato transita
    cap_politica,             # 5% — sleeve de ativo digital aprovável por board
    teto_stablecoin,          # teto de depeg (ES, do Depeg Engine)
    1 - reserva_frac,         # NUNCA invade a reserva de cash
)

# 4. Haircut de liquidez: o ES desconta o valor de liquidez da stablecoin
valor_liquidez = stablecoin_frac × total × (1 - es)
```

**Resultado com o perfil de referência (escala Nubank):** stablecoin = **4,37%** do caixa. Corporativamente sadio. Antes: 50–60% (indefensável).

---

### 3.9 `custo_carrego.py` — o 3º pilar (Capital Markets & Funding)

```python
spread_pct = max(0, taxa_referencia - yield_atual)   # nunca negativo
gap_anual  = valor_parado × spread_pct / 100
```
- **BRL** → referência **CDI** (14,15% a.a.)
- **USD** → referência **T-bill** (3,71% a.a.)

**A tese:** o capital de uma tesouraria **dorme na reserva**, não no giro. Stablecoin é 4,4% do caixa e transita em dias — yield ali é irrelevante. A reserva é ~43% do caixa e fica parada o ano inteiro.

**Com o perfil de referência:** reserva de R$300M + US$73M parados = **R$ 56,2M/ano deixados na mesa** (R$154k/dia).

**E o pulo do gato:** fundo DI / money market / T-bill **continuam sendo cash-equivalents** — mover a reserva para lá **não muda o perfil de risco nem o compliance**. É captura de valor **sem risco adicional**. Não viola a regra de reserva do ADR-0009.

---

## 4. A trilha de decisões (ADR 0001 → 0010)

| ADR  | Decisão                                                                | Status                          |
| ---- | ---------------------------------------------------------------------- | ------------------------------- |
| 0001 | Fontes de dados gratuitas                                              | Accepted                        |
| 0002 | Streamlit + módulos Python                                             | Proposed                        |
| 0003 | **Pivot**: heurística 50/30/20 → Depeg Risk Engine (VaR/ES) + Postgres | Accepted                        |
| 0004 | Parâmetros do motor de risco (faixas, 97%, 90d)                        | Accepted                        |
| 0005 | SQLAlchemy (schema único) + Postgres em Docker                         | Accepted                        |
| 0006 | Deploy: Streamlit Cloud + Neon                                         | Accepted                        |
| 0007 | Yield/opportunity cost + slippage; **hedge real rejeitado**            | ⚠️ **Partially Superseded** (§B) |
| 0008 | Custo honesto do Rail Comparator (on/off-ramp, segmentação)            | Accepted                        |
| 0009 | **Conformidade com tesouraria corporativa**                            | Accepted                        |
| 0010 | 3º pilar reenquadrado: custo de carrego da reserva                     | Accepted                        |

### As três decisões que mais ensinam

**ADR-0003 — o pivot.** O Optimizer alocava por heurística fixa (50/30/20) sem base nenhuma. Não era modelo, era **chute com aparência de modelo**. A frase do ADR: *"qualquer avaliador técnico reconhece como número inventado — e isso mina a credibilidade dos outros módulos que são rigorosos."* Lição: **um número mágico num módulo contamina a percepção do sistema inteiro.**

**ADR-0007 — a decisão que foi rejeitada, e por quê.** Uma revisão externa sugeriu adicionar **hedge real** (comprar put option DeFi contra o USDC). Foi **rejeitado**: viola o escopo negativo do ADR-0003 (*"nunca integra custodian/exchange real"*). E a versão "fake" (só exibir "hedge sugerido") foi rejeitada também — não agrega informação além do que o Optimizer já comunica ao reduzir a alocação. **Decoração sem substância.** Lição: dizer não, com o motivo registrado, é parte do trabalho.

**ADR-0010 — a decisão que matou uma decisão anterior.** O ADR-0007 aceitou implementar "yield sobre a stablecoin parada". Mas o ADR-0009 **mudou a premissa**: stablecoin virou capital de giro em trânsito, não reserva parada. Render yield em dinheiro que fica dias no trilho é **irrelevante**. O 3º pilar foi reenquadrado para onde o capital realmente dorme: a reserva de cash. **Lição: quando a premissa morre, o ADR morre junto — e isso precisa ser registrado, não varrido.** O ADR-0007 foi marcado `Partially Superseded`, com nota explicando o quê e por quê.

---

## 5. A auditoria — onde o projeto estava errado

Nove achados (2026-07-14). A **ironia central**:

> O módulo matematicamente sofisticado (Depeg Engine) estava **sólido**. O módulo de aritmética trivial (Rail Comparator) carregava os **dois furos mais graves** — e justo na vitrine que vende o projeto.

| #        | Achado                                                                                   | Correção                              |
| -------- | ---------------------------------------------------------------------------------------- | ------------------------------------- |
| **F1** 🔴 | Custo do trilho stablecoin = só gas. `usdt_brl`/`usdc_brl` calculados e **nunca usados** | ADR-0008: on-ramp + gas + off-ramp    |
| **F2** 🔴 | PIX (custo 0) vencia **toda** comparação, inclusive contra Wire — apples-to-oranges      | ADR-0008: segmentação por caso de uso |
| **F3** 🟠 | Otimizador dava **duas alocações contraditórias** (reserva absoluta vs. % )              | ADR-0009: alocação única              |
| **F4** 🟡 | ES = média de só **3 amostras** (cauda rasa)                                             | `tamanho_cauda()` + disclaimer na UI  |
| **F5** 🟡 | PTAX fallback **5.0 vs 5.7** entre módulos                                               | `PTAX_FALLBACK` única                 |
| **F6** 🟡 | "Dados on-chain reais" só é verdade **com API key**                                      | Claim corrigido                       |
| **F7** 🟢 | Código morto; `filtrar_trilhos_permitidos` testado mas **desligado**                     | Removido/religado                     |
| **F8** 🟢 | Faixa "médio" é extrapolação sem evento                                                  | Nota no ADR-0004                      |
| **F9** 🟡 | Testes checavam **forma**, não realismo econômico                                        | Testes de propriedade econômica       |

**A lição de F9:** `test_pix_custo_zero` **cristalizava o bug F2** — o teste garantia o comportamento errado. Testes de forma (shape, tipos, soma) não protegem contra erro de **modelagem**. Por isso agora existem testes de **propriedade econômica**: "custo do trilho stablecoin > 0 e inclui conversão", "só trilhos elegíveis entram", "slippage é monotônico no volume", "stablecoin nunca invade a reserva".

---

## 6. Conformidade com finanças corporativas (a parte mais importante)

Esta seção é o que separa o projeto de um "dashboard de cripto".

### 6.1 O fato contábil decisivo

Sob **US GAAP e IFRS**, stablecoin **NÃO é "caixa e equivalentes de caixa"**:
- Não é moeda de curso legal nem depósito à vista.
- Sob a **ASU 2023-08 (FASB)**, cripto é mensurada a **valor justo como ativo** — explicitamente **fora** da linha de caixa no balanço.
- Cash-equivalents são: depósito à vista, fundo money market, **T-bill ≤ 90 dias**. USDC/USDT **não**.

**Consequência que reescreveu o modelo:** a reserva de emergência **tem que ser cash**. Stablecoin **não pode compor a reserva**. Não é "haircut maior" — é **exclusão**.

### 6.2 Como empresa grande realmente opera

```
Tier 1 — Operacional:  dias/semanas de opex, liquidez imediata (folha, fornecedores)
Tier 2 — Reserva/core: buffer de curto prazo em CASH-EQUIVALENT (money market, T-bill)
Tier 3 — Estratégico:  excedente, horizonte maior, yield
+ Backstop:            linha de crédito rotativa (RCF) comprometida
                       ← a liquidez de emergência real não é caixa parado, é a RCF
```

Política de investimento de tesouraria (aprovada pelo **board**) define instrumentos elegíveis, rating mínimo, limites de concentração e tenor. **Ativo digital, se permitido, leva cap rígido (1–5%)** + aprovação específica.

### 6.3 Os dois erros que o modelo tinha

| Erro                               | Por que estava errado                                                                                                                   | Correção                                          |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Reserva = **"3 meses de despesa"** | Heurística de **runway de startup/PME**. Empresa grande dimensiona por **DCOH**, cobertura de dívida, covenants — com RCF como backstop | DCOH configurável (default 60 dias)               |
| Alvo de **50–60% em stablecoin**   | Tesouraria corporativa é **preservação de capital primeiro**. Nenhuma empresa grande aloca metade do caixa em stablecoin                | Working capital no trilho, teto triplo → **4,4%** |

### 6.4 O reuso elegante: ES como haircut

O Expected Shortfall que o Depeg Engine já calcula ganha um **segundo uso legítimo**: é o **haircut de liquidez** da stablecoin — exatamente a métrica corporativa de "quanto desconto aplico neste ativo de risco ao contá-lo como liquidez".

```
valor_liquidez = valor_stablecoin × (1 − ES)
```
Uma métrica, dois papéis: **teto de alocação** e **haircut de liquidez**.

### 6.5 A âncora empírica — e a honestidade sobre ela

Perfil de referência calibrado em **Nu Holdings (Nubank), Form 20-F FY2025** (SEC, 25/02/2026):

| Métrica (REAL)                 | Valor                  |
| ------------------------------ | ---------------------- |
| Receita                        | US$ 15,8 bi (+37% a/a) |
| Lucro líquido                  | US$ 2,9 bi             |
| Caixa & equivalentes (holding) | ~US$ 3,0 bi            |
| Depósitos                      | US$ 41,9 bi            |

⚠️ **Ressalva registrada no código e no ADR:** Nubank é **banco** — balanço dominado por depósitos e carteira de crédito, não por caixa operacional pagando fornecedor no exterior. Usado **só como âncora de ordem de grandeza**. Cada campo do perfil é rotulado **(REAL, com fonte)** ou **(ILUSTRATIVO)**. **Não se afirma que o Nubank aloca em stablecoin.**

> **Essa ressalva é o tipo de coisa que separa rigor de teatro.** Seria fácil (e desonesto) dizer "calibrado em dados do Nubank" e deixar a ambiguidade trabalhar a favor.

---

## 7. O que o projeto NÃO faz (escopo negativo — ADR-0003)

- Sem autenticação/multi-tenant.
- **Sem execução real de transação** (nunca integra custodian/exchange real) ← foi isso que barrou o hedge do ADR-0007.
- Sem assessoria jurídica ou fiscal real (compliance filter tem disclaimer).
- Sem apuração de IR (só IOF).

**Débitos técnicos vivos (20 itens no `AGENTS.md`)** — os que mais importam:
- **#7**: risco medido só sobre USDC, aplicado ao total em stablecoin (USDT tem perfil de reserva distinto).
- **#8**: granularidade diária **subestima** o risco de cauda real.
- **#14/#15/#19/#20**: off-ramp 0,3%, `DIAS_SETTLEMENT`, cap de política e slippage são **premissas**, não medições.

**Por que listar os próprios defeitos?** Porque um avaliador vai encontrá-los de qualquer jeito. Encontrá-los **documentados** sinaliza rigor; encontrá-los **escondidos** destrói a credibilidade do resto.

---

## 8. Como contar a história (5 slides)

1. **Problema**: tesouraria cross-border precisa escolher trilho, obedecer regulação e alocar caixa — sem ferramenta.
2. **Solução**: motor com VaR/ES quantitativo sobre histórico real de peg.
3. **Validação**: o spike do **SVB (mar/2023) aparece sozinho** no gráfico — o modelo descobre a crise sem hardcode.
4. **Resultado**: economia real **~90%** vs. Wire (all-in, conversão contada) — a arbitragem existe porque o stablecoin **dribla o IOF**.
5. **Diferencial**: a arbitragem tem **prazo de validade regulatório** (BCB 561, out/2026). O projeto mede a janela, o risco de depeg de usá-la, e o custo de carrego de não usar o caixa.

**O gancho que fecha:** não é "cripto é grátis". É *"existe uma janela de arbitragem de ~90%, com data de expiração conhecida, e eu sei exatamente quanto risco estou correndo para usá-la."*

---

## 9. Glossário rápido

| Termo                       | Significado                                                            |
| --------------------------- | ---------------------------------------------------------------------- |
| **VaR**                     | Perda no **limiar** da cauda, a dado nível de confiança                |
| **Expected Shortfall (ES)** | Perda **média dentro** da cauda (≥ VaR). Padrão Basel III/FRTB         |
| **Depeg**                   | Desvio do preço da stablecoin em relação à paridade 1:1                |
| **On/Off-ramp**             | Entrada (BRL→stablecoin) e saída (stablecoin→USD) do trilho cripto     |
| **DCOH**                    | *Days cash on hand* — dias de opex cobertos pelo caixa                 |
| **Cash equivalent**         | Depósito à vista, money market, T-bill ≤90d. **Stablecoin não é**      |
| **Haircut de liquidez**     | Desconto no valor de liquidez de um ativo de risco: `valor × (1 − ES)` |
| **Custo de carrego**        | O que a reserva parada deixa de render vs. a referência (CDI/T-bill)   |
| **RCF**                     | *Revolving credit facility* — o backstop real de liquidez corporativa  |
| **eFX**                     | Câmbio eletrônico regulado — onde a BCB 561 proíbe stablecoin          |
| **Backtest**                | Reconstrução do risco ao longo do tempo com janela deslizante          |

---

## 10. Referências

- ADRs: `docs/adr/0001..0010`
- Auditoria: `docs/audit/2026-07-14_auditoria_tecnica_negocio_matematica.md`
- Linguagem Ubíqua + débitos: `AGENTS.md`
- Nu Holdings 20-F FY2025: https://www.sec.gov/Archives/edgar/data/1691493/000129281426002166/nuform20f_2025.htm
- FASB ASU 2023-08 (cripto a valor justo, fora de caixa & equivalentes)
- Basel III / FRTB — Expected Shortfall 97,5% como métrica regulatória
