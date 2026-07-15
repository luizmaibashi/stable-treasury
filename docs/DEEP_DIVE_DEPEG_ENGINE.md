# Deep Dive — Depeg Risk Engine (as 5 perguntas)

> **Propósito**: entender o coração quantitativo do projeto a ponto de defendê-lo numa banca / entrevista / mesa. Base para o README e para a story de pitch.
> **Método**: toda afirmação numérica aqui foi computada sobre **dado real** (DefiLlama, série diária USDC 2022→2026, 1.653 pontos), não estimada.
> **Data**: 2026-07-14

---

## Pergunta 1 — O que é Expected Shortfall (ES)?

### A intuição
Imagine que você lista **todos os dias ruins** de uma stablecoin (quanto ela caiu abaixo de US$1,00). Ordena do pior pro menos pior. Agora olha só a **pior fatia de 3%** desses dias.

- **VaR (Value at Risk) 97%** responde: *"Qual é a perda no **limiar** dessa pior fatia de 3%?"* — é uma **fronteira**.
- **Expected Shortfall (ES) 97%** responde: *"Dado que estou dentro dessa pior fatia de 3%, qual é a perda **média** ali dentro?"* — é a **média da cauda**.

### Por que ES e não VaR
VaR tem um buraco fatal: ele te diz **onde** a cauda começa, mas **nada** sobre quão fundo ela vai. Duas stablecoins podem ter o mesmo VaR de 2% e uma delas, nos piores casos, cair 3% e a outra cair 90%. **O VaR não distingue as duas. O ES sim.**

Por isso **Basel III / FRTB** (a regra de risco de mercado dos bancos pós-2008) **abandonou o VaR 99% e adotou o ES 97,5%** — exatamente porque o VaR foi cego para as caudas gordas que quebraram bancos em 2008. Adotar ES no projeto = *"meço risco como um regulador bancário mede, não como um tutorial mede."*

### A matemática (com o código)
```python
def var_es_historico(retornos, confianca=0.97):
    perdas = -retornos                        # depeg = perda; inverte o sinal
    perdas_ordenadas = np.sort(perdas)[::-1]  # pior perda primeiro
    n = len(perdas_ordenadas)
    tail_count = tamanho_cauda(n, confianca)  # quantos dias formam os "3% piores"
    var = perdas_ordenadas[tail_count - 1]    # LIMIAR da cauda  → VaR
    es  = perdas_ordenadas[:tail_count].mean()# MÉDIA na cauda   → ES
    return var, es
```

### Exemplo numérico com dado real (janela do SVB)
Na janela de 90 dias terminada em **2023-03-19**, os 3 piores desvios de peg do USDC foram aproximadamente **−1,68%, −1,76%, −1,85%**.
- `tail_count = round(0,03 × 90) = 3`
- **VaR(97%)** = o menos pior dos 3 = **1,68%** (o limiar)
- **ES(97%)** = média dos 3 = **1,763%** (a cauda inteira)

**ES > VaR sempre** — porque é a média de tudo que é pior que o limiar.

### A escolha de métrica que quase ninguém acerta
O projeto **não** usa retorno diário (`(p_t − p_{t-1})/p_{t-1}`), que é o padrão em ações/FX. Usa **desvio do peg** (`preço − 1,00`).

> Por quê? Uma stablecoin que escorrega de US$1,00 → US$0,90 em **30 passos pequenos** tem retorno diário quase zero em cada passo — o modelo de retorno **não veria o depeg acontecer**. O desvio do peg revela o buraco a qualquer instante, porque mede distância da paridade, não variação entre dias.

Consequência técnica elegante (ADR-0011): como desvio é um **nível** (não um retorno), **não há regra do √t** — misturar granularidade diária e horária é livre, sem reescala. Por isso o upgrade para horário foi limpo.

---

## Pergunta 2 — Por que calibrar com 90 dias + confiança 97%?

### Janela de 90 dias (1 trimestre)
Três razões, todas defensáveis:
1. **Cadência de attestation.** Circle e Tether publicam a composição das reservas **trimestralmente**. A janela de risco casa com o ciclo de informação real sobre o lastro.
2. **Regime atual, não história antiga.** Janela longa demais (ex: 2 anos) **dilui** o risco de hoje com calmaria antiga. Curta demais vira ruído. Um trimestre captura o regime vigente.
3. **É o horizonte de decisão de uma tesouraria** — planejamento de caixa trimestral.

### Confiança de 97%
Não é número redondo arbitrário — é **alinhamento a Basel III / FRTB**, que padronizou **ES a 97,5%** como a métrica regulatória de risco de mercado. Adotar ~97% coloca o modelo no mesmo nível de conservadorismo que um banco usa.

### A fragilidade que assumimos abertamente (e como foi resolvida)
90 dias × 3% = **3 dias na cauda** (diário). Três pontos é uma cauda **rasa** — o ES fica ruidoso e sensível a um único outlier. **Isso foi resolvido no ADR-0011:** o risco atual passou a usar **série horária** — 90 dias = ~2.160 pontos → cauda de **~65 horas**, estatisticamente robusta, e captura o mínimo intra-dia real (o diário suavizava).

---

## Pergunta 3 — Quais datas têm spike no gráfico? Por quê?

### O que o dado real diz (computado sobre 2022→2026)
Rodando o ES rolante (90d, 97%, passo 7d) sobre toda a história do USDC:

| Rank | Data (fim da janela) | ES(97%) | Faixa |
|------|----------------------|---------|-------|
| 1 | **2023-03-19** | **1,763%** | baixo |
| = | 2023-03-26 → 2023-04-22 | **1,763%** (travado) | baixo |

- **Mínimo de preço diário**: **0,9603** em **2023-03-12**.
- **Mínimo intra-dia real (horário)**: **0,8767** — o diário suavizava para ~0,96.

### Por que o spike existe: o colapso do SVB (março/2023)
O **Silicon Valley Bank** quebrou em 10/mar/2023. A **Circle** (emissora do USDC) tinha **US$ 3,3 bilhões** das reservas do USDC depositados exatamente lá. Quando o mercado soube, entrou em pânico: se as reservas estavam presas, o USDC não teria lastro para honrar o resgate 1:1. O USDC **despegou para ~US$ 0,88** (intra-dia). Recuperou quando o **Fed/FDIC garantiu os depósitos do SVB** — as reservas estavam seguras, o peg voltou em dias.

**Esse é o teste de validação mais forte do projeto**: o spike aparece **sozinho** no gráfico, sem nenhum hardcode de data. O modelo *descobre* a crise porque o preço real caiu naquela janela. Se você me perguntar "como sei que o motor funciona?", a resposta é: *ele detectou o SVB sem que ninguém dissesse a ele que o SVB aconteceu.*

### O detalhe que ensina como o ES rolante funciona
Repare que o ES fica **travado em exatamente 1,763% de 19/mar até ~22/abr** — mais de um mês no mesmo valor. Por quê? Porque a **janela móvel de 90 dias** continua incluindo os 3 dias piores do depeg (10-13/mar). O ES só cai quando esses dias **saem** da janela, ~90 dias depois. Isso mostra visceralmente que o ES é uma **memória de 90 dias** — a crise "pesa" no risco enquanto estiver na janela, e some abruptamente quando expira.

### A âncora de calibração (por que as faixas são o que são)
O USDC-SVB (recuperável) deu **ES = 1,76% → faixa "baixo"**. O outro âncora, **UST/Terra (mai/2022)**, foi catastrófico e nunca recuperou → **ES ≈ 99,3% → faixa "alto"**. As faixas do modelo (`baixo <5%`, `medio <30%`, `alto ≥30%`) são calibradas nesses dois pontos reais. **Honestidade (débito F8):** a faixa "médio" (5-30%) não tem nenhum evento observado dentro — é buffer entre um caso recuperável e um catastrófico, não calibração direta.

---

## Pergunta 4 — Você é CFO e vê ES = 24%. O que faz?

Primeiro, **ler o número corretamente**: ES(97%) = 24% significa *"nas piores 3% das horas, o USDC perde em média 24% do peg"* — ou seja, negocia perto de **US$ 0,76** nos piores cenários. Isso **não** é um blip como o SVB (1,76%). É um regime de estresse severo, a caminho de território UST. **24% cai na faixa "médio" (teto 30%)**, mas está no topo dela — a um passo do "alto".

### O que o sistema faz automaticamente
- **Teto de alocação** cai para 30% do sleeve de stablecoin.
- **Haircut de liquidez**: o valor de liquidez da stablecoin é descontado — `valor × (1 − 0,24)` = só **76%** conta como liquidez real.

### O que o CFO faz (ação humana, não automática)
1. **Parar de rotear novo fluxo** pelo trilho stablecoin. A arbitragem de custo (~90% vs Wire) **não compensa** um risco de cauda de 24% — a economia de 2-6% no custo é anã perto de uma perda potencial de 24% no principal.
2. **Acelerar o settlement** do que já está em trânsito. Working capital no trilho deve **sair rápido** — converter USDT→USD/BRL o quanto antes, mesmo pagando mais slippage. Reduzir a duração da exposição.
3. **Voltar pro Wire**, apesar do custo. É o momento em que o trilho "caro e chato" (SWIFT regulado) vale o prêmio — porque o risco do trilho barato explodiu.
4. **Diferenciar por emissor.** ES=24% da carteira pode estar concentrado num emissor (ex: USDT com dúvida de reserva) enquanto o outro está calmo. O `avaliar_risco_carteira` (ADR-0011) mede a composição real — o CFO reponderaria para o emissor mais sólido.
5. **Não tocar na reserva.** A reserva já é **cash** (BRL/USD), não stablecoin (ADR-0009) — então o caixa de emergência **não é afetado** pelo depeg. Essa é a tranquilidade que a arquitetura compra: a crise do trilho não contamina a liquidez de sobrevivência.

**Resumo da postura**: ES=24% é sinal de **retração**, não de pânico. O sistema não "foge" sozinho — ele **quantifica** para o humano decidir com número, não com medo.

---

## Pergunta 5 — A story em 5 slides

**Slide 1 — O problema.** Uma tesouraria de fintech (ou aérea, ou importador) que paga no exterior precisa escolher trilho, obedecer a regulação e alocar caixa — hoje, sem ferramenta que junte as três coisas.

**Slide 2 — A solução.** Um motor que mede risco de stablecoin com **VaR / Expected Shortfall** (o padrão Basel) sobre **histórico real de peg**, não sobre opinião.

**Slide 3 — A validação.** O spike do **colapso do SVB (mar/2023)** aparece **sozinho** no gráfico histórico — o modelo detecta a crise sem que ninguém a programe. *Prova de que o motor funciona.*

**Slide 4 — O resultado.** Economia real **~90% vs. Wire** num pagamento cross-border de serviços — **all-in, com a conversão contada** (não o "99,99%" fictício). E a economia existe porque o stablecoin **dribla o IOF de câmbio**.

**Slide 5 — O diferencial.** Essa arbitragem tem **prazo de validade regulatório**: a **BCB 561 fecha a janela em out/2026**. O projeto é o único que mede, ao mesmo tempo: **a janela** (quanto se economiza), **o risco de usá-la** (ES de depeg) e **o custo de não usar o caixa** (carrego da reserva vs CDI/T-bill).

### O gancho que fecha
> Não é *"cripto é grátis"*. É: **"existe uma janela de arbitragem de ~90%, com data de expiração conhecida, e eu sei exatamente quanto risco estou correndo para usá-la — medido como um banco mede."**

---

## Apêndice — números-chave para ter na ponta da língua

| Fato | Valor | Fonte |
|------|-------|-------|
| Pior evento real do USDC (ES) | **1,76%** | SVB mar/2023, computado |
| Mínimo diário USDC | 0,9603 (12/mar/2023) | DefiLlama |
| Mínimo intra-dia real | **0,8767** | DefiLlama horário |
| Evento catastrófico (âncora "alto") | ES ≈ 99,3% | UST mai/2022 |
| Confiança / janela | 97% / 90 dias | Basel FRTB / attestation |
| Cauda (diário → horário) | 3 → ~65 amostras | ADR-0011 |
| Economia stablecoin vs Wire (serviços) | ~90% all-in | cálculo do comparador |
| Prazo da arbitragem | out/2026 | Resolução BCB 561 |
