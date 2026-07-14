# ADR-0008: Modelo de custo honesto do Rail Comparator (spread on/off-ramp + segmentação por caso de uso)

**Data**: 2026-07-14
**Status**: Accepted
**Contexto**: auditoria técnica/negócio/matemática 2026-07-14 (`docs/audit/2026-07-14_auditoria_tecnica_negocio_matematica.md`), achados F1 e F2 — os dois furos críticos que invalidavam a manchete de economia do projeto.

---

## 1. CONTEXTO (O QUÊ?)

O Rail Comparator — porta de entrada visual e fonte da narrativa de venda ("99,99% economia") — tinha dois erros de modelagem que não sobreviviam a escrutínio técnico:

- **F1**: custo do trilho stablecoin = **só gas**. As variáveis `usdt_brl`/`usdc_brl` (preço real de conversão) eram calculadas e nunca usadas. Ignorava o custo de entrar/sair do trilho cripto.
- **F2**: PIX tinha custo `0` fixo e vencia **toda** comparação, inclusive contra Wire — comparando um trilho doméstico (BRL) com trilhos cross-border, casos de uso diferentes.

Consequência: a economia de 99,99% era parcialmente fictícia e a comparação era apples-to-oranges. O risco reputacional que o ADR-0003 combateu no Optimizer ("número inventado mina credibilidade") havia migrado para o módulo mais visível.

---

## 2. DECISÃO (POR QUÊ?)

### 2.1 Trilho stablecoin como jornada de 3 pernas (F1)

Uma tesouraria não "tem USDT" — tem BRL e precisa de USD lá fora. O custo real:

```
BRL ─(1) compra USDT─► USDT ─(2) gas─► USDT ─(3) vende─► USD
    prêmio on-ramp          (já modelado)    spread off-ramp
```

**Custo total stablecoin = spread_onramp + gas + spread_offramp**

- **On-ramp** (perna 1): derivado de dado real de mercado. `premio = max(0, preco_stablecoin_brl / ptax − 1)`. Ressuscita `usdt_brl`/`usdc_brl`. Fallback se API cair: **0,5% USDT / 0,3% USDC** (mesmos números que já estavam no fallback morto).
- **Off-ramp** (perna 3): constante conservadora **0,3%** — venda stablecoin→USD em mercado profundo é quase 1:1. Escolha registrada, não medida (débito técnico).

### 2.2 Segmentação por caso de uso (F2)

`comparar_custos` passa a receber `caso_uso`:
- **`domestico`** (BRL→BRL): trilho elegível = **PIX**.
- **`cross_border`** (converte BRL↔USD): elegíveis = **Wire, USDT, USDC**. PIX **não** entra.

PIX deixa de "vencer" comparações que não disputa. Perfis sintéticos rodam em `cross_border`, onde a escolha importa.

### 2.3 Religação do filtro legal (F7)

`comparar_custos` aceita `eletronico_cambio: bool`. Quando `True` (eFX), aplica `filtrar_trilhos_permitidos` (BCB 561) e remove USDT/USDC dos candidatos — a função antes testada-mas-desligada ganha uso real no fluxo do produto.

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- Manchete honesta e mais sofisticada: num cross-border de R$50k, **USDC ≈ 0,8% all-in vs. Wire ≈ 6% (spread FX 2,5% + IOF 3,5% + tarifa)** → economia real **~85%**, defensável.
- Narrativa ganha profundidade: a economia existe porque o stablecoin **dribla o IOF de câmbio** — a arbitragem regulatória que a **BCB 561 fecha em out/2026**. Deixa de ser "cripto grátis" e vira "janela de arbitragem de ~85% com prazo de validade regulatório", alinhado ao gancho BCB (diferencial do projeto).
- `usdt_brl`/`usdc_brl` deixam de ser código morto; `filtrar_trilhos_permitidos` deixa de ser função órfã.

**Negativas / débitos:**
- Off-ramp 0,3% é constante estimada, não medida (novo débito técnico).
- On-ramp assume que o prêmio de compra à vista aproxima o custo de conversão de grande volume — não modela profundidade de book/slippage por tamanho (isso é o ponto C do ADR-0007, ainda pendente e agora convergente com este modelo).

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê rejeitada |
|-------|----------------------|
| Manter custo stablecoin = só gas | Modelo fictício; furo no módulo mais visível (F1) |
| Off-ramp 0,1% | Otimista demais; fácil de um avaliador contestar |
| On-ramp só constante fixa (sem mercado) | Perde o "dado on-chain real" que é diferencial do projeto |
| Comparar todos os trilhos sem segmentar | Mantém o apples-to-oranges do F2 (PIX vs Wire) |

---

## 5. IMPACTO & VALIDAÇÃO

**Métrica de sucesso:** testes de propriedade econômica (F9) — custo stablecoin > 0 e inclui componente de conversão; só trilhos elegíveis ao caso de uso entram; eFX remove stablecoin. Narrativa de economia atualizada em `DIRECAO_DO_PLANO.md`.

**Risco de regressão:** muda os números exibidos e a story. Testes antigos que cristalizavam o bug (`test_pix_custo_zero` em comparação cross-border) precisam ser revistos.

---

## 6. LINKS RELACIONADOS

- `docs/audit/2026-07-14_auditoria_tecnica_negocio_matematica.md` (F1, F2, F7 que originaram este ADR)
- `docs/adr/0007-yield-opportunity-cost-e-slippage-heuristico.md` (ponto C — slippage por volume, convergente com o on-ramp deste ADR)
- `src/comparador.py` (implementação), `src/compliance.py::filtrar_trilhos_permitidos` (filtro religado)