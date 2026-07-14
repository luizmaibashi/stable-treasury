# Auditoria Técnica + Negócio + Matemática — StableTreasury

**Data**: 2026-07-14
**Escopo**: verificação completa dos 10 módulos `src/` + `app.py`, cruzando corretude técnica, racional de negócio e matemática.
**Método**: leitura integral + grep de uso real (código morto) + leitura dos testes (o que de fato validam).
**Status dos achados**: **RESOLVIDOS na mesma sessão** (2026-07-14). F1/F2/F7 → ADR-0008. F3 + conformidade corporativa → ADR-0009 (reserva cash-only, stablecoin como working capital, âncora Nubank FY2025). F4/F5/F6/F8 → correções diretas. F9 → testes de propriedade econômica. Suite: 53 passed. Débitos rastreados em `AGENTS.md` (#12-#17).

---

## Sumário executivo

O **núcleo quantitativo (Depeg Risk Engine) é sólido e defensável**. A ironia da auditoria: o módulo matematicamente sofisticado (`depeg_risk.py`) está bem calibrado, enquanto o módulo de **aritmética trivial (`comparador.py`)** — que é a primeira impressão do produto e a fonte da manchete de marketing ("99,99% economia") — carrega os dois furos de modelagem de negócio mais graves.

Severidade dos achados:

| # | Achado | Camada | Severidade | Toca a "story"? |
|---|--------|--------|-----------|-----------------|
| F1 | Custo do trilho stablecoin ignora spread de on/off-ramp | comparador | 🔴 Crítico | **Sim — invalida a manchete** |
| F2 | PIX domina incondicionalmente (comparação apples-to-oranges) | comparador | 🔴 Crítico | **Sim — invalida a manchete** |
| F3 | Otimizador tem duas lógicas de alocação inconsistentes | otimizador | 🟠 Alto | Sim (recomendação ao CFO) |
| F4 | ES calculado sobre cauda de 3 amostras (ruído estatístico) | depeg_risk | 🟡 Médio | Não (rigor interno) |
| F5 | PTAX fallback divergente (5.0 vs 5.7) entre módulos | coletor/otimizador | 🟡 Médio | Não |
| F6 | "Dados on-chain reais" só é verdade com API keys | coletor | 🟡 Médio | Sim (claim do AGENTS.md) |
| F7 | Código morto (TIPO_TRANSACAO, usdt_brl/usdc_brl, filtro não ligado) | vários | 🟢 Baixo | Não |
| F8 | Faixa "médio" é extrapolação sem evento observado | depeg_risk | 🟢 Baixo | Não (já ~documentado) |
| F9 | Testes são shape/smoke — não validam realismo econômico | tests | 🟡 Médio | Indireto |

---

## F1 — 🔴 Custo do trilho stablecoin ignora o spread de on/off-ramp

**Evidência técnica:** `comparador.py:14-15` calcula `usdt_brl` e `usdc_brl`, mas grep confirma que **essas variáveis nunca são usadas** no cálculo de custo. Os trilhos USDT/USDC (`_calcular_usdt_*`, `_calcular_usdc_*`) somam **apenas gas fee**.

**Furo de negócio/matemática:** o custo real de usar um trilho stablecoin numa tesouraria não é só o gas. É um round-trip:
1. **Comprar** USDT com BRL → paga prêmio ~0,5–1% sobre a PTAX (o próprio código estimava `ptax * 1.005`)
2. **Transferir** on-chain → gas (o único componente hoje modelado)
3. **Receptor vende** USDT → BRL/USD → desconto ~0,5–1%

Round-trip real ≈ **1–2% do valor**, comparável ao spread de um wire (2,5%), **não** "custo ~zero". O modelo atual subestima o custo do trilho stablecoin em ~1-2 ordens de grandeza.

**Consequência:** a manchete "R$ 50k → USDT custa só R$X de gas (99,99% economia vs Wire)" é **parcialmente fictícia** — ela desaparece quando o spread de conversão entra na conta. Um avaliador de fintech/cripto identifica isso em segundos, e o furo está justamente no número mais vendável do projeto.

**Ligação com revisão externa:** é exatamente o **ponto C do artigo** (liquidez/slippage do próprio rail) — que o ADR-0007 aceitou implementar como heurística. F1 é a versão dura desse mesmo ponto: não é refinamento futuro, é erro presente.

---

## F2 — 🔴 PIX domina incondicionalmente (comparação apples-to-oranges)

**Evidência técnica:** `_calcular_brl_pix` retorna custo total `0.0` fixo. `gerar_faturas_sinteticas` pega `melhor = custos[0]` (menor custo). Como PIX é sempre 0, **o "melhor trilho" é sempre PIX**, para qualquer valor e qualquer perfil.

**Furo de negócio:** PIX é liquidação **doméstica em BRL**. Não faz pagamento internacional. Se a fintech precisa pagar um fornecedor nos EUA, PIX **não é uma opção elegível** — comparar PIX com Wire/USDC é comparar trilhos que servem casos de uso diferentes. A tabela de perfis sintéticos hoje diz "melhor trilho = PIX, R$0" para 100% dos casos, o que é economicamente vazio.

**A correção já existe no código, mas está desligada:** `filtrar_trilhos_permitidos` (`compliance.py:50`) faz exatamente a filtragem de elegibilidade — mas grep confirma que **só é chamada num teste, nunca no `app.py`**. A eligibilidade nunca é aplicada no fluxo real.

**Correção de arquitetura:** o comparador precisa receber o **caso de uso** (pagamento doméstico vs. cross-border) e comparar só os trilhos elegíveis. Doméstico: PIX vs. TED. Cross-border: Wire vs. USDT vs. USDC. Aí a economia comparada passa a ser real (USDC vs. Wire, ambos cross-border) — e a manchete vira defensável.

---

## F3 — 🟠 Otimizador tem duas lógicas de alocação inconsistentes

**Evidência técnica:** `otimizar_alocacao` produz, no mesmo retorno, **duas recomendações que não conversam**:
1. **Baseada em reserva** (linhas 38-52): `brl_target`, `manter_usd`, `converter_usdt_para_brl` — em valores absolutos (R$/US$)
2. **Baseada em percentual** (`_gerar_sugestao`, string): "40% BRL / 20% USDT / 10% USDC" — em % do total

Elas não são reconciliadas. Exemplo concreto: `manter_usd` (exportador) = `saldo_usd + previsao_recebimento*0.3` (um valor absoluto em USD), enquanto a `sugestao` diz "30% USD do total_brl" (outro número em USD). **São dois valores de USD diferentes na mesma tela.**

**Furo de negócio:** um CFO lendo o output recebe instrução conflitante — "converta USDT→BRL até 3 meses de reserva" **e** "aloque 40% BRL / 20% USDT / 10% USDC", sem saber qual prevalece. O módulo cujo propósito é *decidir alocação* entrega duas alocações.

**Correção:** escolher uma fonte única de verdade. Recomendação: a alocação percentual (que já integra o teto de risco do Depeg Engine) deve ser a saída canônica; a lógica de reserva vira uma **restrição** (piso de BRL) aplicada *antes* de distribuir o resto, não uma recomendação paralela.

---

## F4 — 🟡 ES calculado sobre cauda de 3 amostras

**Matemática:** `avaliar_risco_atual` usa `dias=90`, `confianca=0.97`. Logo `tail_count = round(0.03 × 90) = round(2.7) = 3`. O **ES "atual" é a média dos 3 piores dias** de uma janela de 90. Três pontos é uma cauda estatisticamente rasa — o ES resultante tem variância alta e é sensível a um único outlier.

Não é bug (a matemática está correta), é **limitação de robustez**: historical simulation com janela curta + confiança alta produz estimador de cauda ruidoso. Combinado com o débito #8 (granularidade diária suaviza o mínimo intradiário), o ES "atual" pode oscilar bastante semana a semana.

**Mitigações possíveis:** (a) reportar na UI o nº de observações na cauda (transparência); (b) janela maior só para o cálculo "atual"; (c) suavização (ES médio de N janelas). Nenhuma é obrigatória — mas o número merece um disclaimer de robustez, não ser mostrado como pontual preciso.

---

## F5 — 🟡 PTAX fallback divergente entre módulos

`comparador.py:13` usa `ptax_venda() or 5.0`; `otimizador.py:20` usa `ptax_venda() or 5.7`. Mesmo câmbio USD/BRL, dois fallbacks (14% de diferença). Se a PTAX cair numa sessão que usa os dois módulos, cada um calcula câmbio diferente pro mesmo instante — inconsistência interna que nenhum teste unitário isolado pega.

**Correção trivial:** constante compartilhada `PTAX_FALLBACK` num só lugar (candidato: `coletor_precos.py`, ao lado de `ptax_venda`).

---

## F6 — 🟡 "Dados on-chain reais" só é verdade com API keys

Regra do AGENTS.md: *"Dados on-chain reais: CoinGecko (preço), Etherscan (gas fee estimado)"*. Mas `gas_fee_eth`/`gas_fee_polygon` exigem `ETHERSCAN_API_KEY`/`POLYGONSCAN_API_KEY`. Sem as chaves (deploy padrão de portfolio), `apikey=""` → API retorna erro → **fallback hardcoded (20/50 gwei) sempre ativo**. Ou seja, no deploy público sem keys, o gas exibido é constante inventada, não on-chain.

**Risco adicional a verificar:** o endpoint `gastracker` da Etherscan v1 está em depreciação para a API v2 multichain — pode parar de responder, tornando o fallback permanente sem aviso. **Não confirmado nesta auditoria — requer teste ao vivo.**

**Correção:** ou (a) garantir keys no deploy e falhar visível se ausentes, ou (b) rebaixar o claim do AGENTS.md para "gas estimado (on-chain quando key disponível, senão faixa fixa)" — honestidade sobre o que o deploy realmente faz.

---

## F7 — 🟢 Código morto

- `compliance.py:10` `TIPO_TRANSACAO` — dict definido, nunca referenciado.
- `comparador.py:14-15` `usdt_brl`/`usdc_brl` — calculados, nunca usados (raiz do F1).
- `compliance.py:50` `filtrar_trilhos_permitidos` — testado, mas não ligado ao `app.py` (raiz do F2).

Remover o morto de verdade; **religar** `filtrar_trilhos_permitidos` (é a peça que conserta F2, não deletar).

---

## F8 — 🟢 Faixa "médio" é extrapolação

`FAIXAS_RISCO` calibrada com 2 pontos reais (USDC-SVB = 1,76% → baixo; UST = 99,32% → alto). A faixa "médio" (5%–30%) **não tem nenhum evento histórico observado dentro dela** — é interpolação de bom senso entre um caso recuperável e um catastrófico. Já parcialmente reconhecido no comentário do código. Aceitável; só merece nota explícita no ADR-0004 de que "médio" é buffer, não faixa calibrada.

---

## F9 — 🟡 Testes validam forma, não realismo econômico

Os 473 linhas de teste checam shape (nº de colunas, tipos, soma = 100%, ordenação) e smoke. **Nenhum teste pegaria F1, F2 ou F3** — não há assert de que o custo de um trilho seja economicamente realista, nem de que a alocação recomendada seja internamente consistente. `test_pix_custo_zero` inclusive *cristaliza* o bug F2 (assere que PIX = 0 como comportamento esperado).

**Correção:** ao consertar F1-F3, adicionar testes de propriedade econômica (ex: "custo do trilho stablecoin > 0 e inclui componente de conversão"; "só trilhos elegíveis ao caso de uso entram na comparação"; "otimizador retorna uma única alocação coerente que soma 100%").

---

## Conformidade com o negócio do projeto

**O que está em conformidade:** Depeg Risk Engine + persistência + backtest cumprem a proposta de "rigor quantitativo defensável sobre dado real" — é o diferencial de portfolio prometido no ADR-0003, e entrega.

**O que NÃO está:** o Rail Comparator, que é a porta de entrada visual e a fonte da narrativa de venda, viola a própria promessa de rigor — F1 e F2 fazem a manchete de economia não sobreviver a escrutínio técnico. Como o ADR-0003 alertou sobre a heurística 50/30/20 ("qualquer avaliador reconhece como número inventado — mina a credibilidade dos outros módulos"), **o mesmo risco reputacional agora mora no comparador**: um furo no módulo mais visível contamina a percepção do núcleo sólido.

**Veredito:** o projeto está tecnicamente sólido no miolo e frágil na vitrine. Prioridade de correção deve ser invertida em relação à sofisticação: consertar a aritmética simples do comparador (F1/F2) vale mais, agora, que refinar o motor de risco.

---

## Plano de correção proposto (para aprovação)

**Lote 1 — trivial, sem risco à narrativa (posso fazer já):**
- F5 (constante PTAX única), F7 (remover código morto / religar filtro), F8 (nota no ADR-0004)

**Lote 2 — conserta a manchete (muda números, precisa decisão de produto):**
- F2: segmentar comparador por caso de uso + religar `filtrar_trilhos_permitidos`
- F1: incluir spread de on/off-ramp no custo do trilho stablecoin (converge com ponto C / ADR-0007)
- Refazer a narrativa de economia para "USDC vs. Wire, ambos cross-border" (defensável)

**Lote 3 — coerência e rigor:**
- F3 (alocação única no otimizador), F4 (disclaimer/robustez do ES), F6 (honestidade do claim on-chain), F9 (testes de propriedade econômica)

Cada lote precede código com ADR quando muda decisão (F1/F2/F3 mudam decisão de modelagem → ADR-0008).