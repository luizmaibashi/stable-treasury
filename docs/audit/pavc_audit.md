# PAVC Audit — StableTreasury

**Data**: 2026-07-04
**Framework**: Maibashi PAVC (Advogado do Diabo, Explicabilidade, Falsificabilidade)

---

## 1. ADVOGADO DO DIABO

### Falha 1: Gas fee estimado não reflete execução real
- **Crítica**: Gas fee da Etherscan é uma estimativa do próximo bloco, não o custo real de uma transação USDT ERC-20 (que pode ser 2-3x maior com dados de contrato)
- **Impacto**: Subestimação de custo dos trilhos on-chain em até 3x
- **Mitigação**: Adicionar margem de segurança de 2x no gas fee estimado

### Falha 2: Spread bancário é fixo (2.5%), mas varia por banco e volume
- **Crítica**: Bradesco, Itaú, Santander têm spreads diferentes; clientes corporativos negociam spreads melhores
- **Impacto**: O comparador superestima custo Wire para grandes volumes
- **Mitigação**: Adicionar slider de spread customizável no dashboard

### Falha 3: IOF sobre stablecoin é tratado como 0%, mas há contencioso
- **Crítica**: IN RFB 1888/2019 diz que cripto não é moeda, mas RFB já autuou empresas que usam stablecoin como moeda de câmbio
- **Impacto**: Risco fiscal não modelado
- **Mitigação**: Nota no README: "Alíquotas de IOF conforme decretos vigentes. Transações com stablecoin podem estar sujeitas a interpretações divergentes da RFB."

---

## 2. EXPLICABILIDADE

### Bom
- Cálculo de custo por trilho é determinístico e rastreável
- IOF vem de tabela YAML pública com referência ao decreto
- Compliance Filter expõe quais resoluções foram aplicadas

### Ruim
- Preço do gas fee não mostra breakdown (gwei × gas units × preço ETH)
- Liquidity Optimizer não explica heurística de alocação (50/30/20)
- Spread bancário não tem trace de fonte (B3/FEBRABAN não linkado)

---

## 3. FALSIFICABILIDADE

### Testes que podem quebrar
| Teste | Condição de falha | Risco |
|-------|-------------------|-------|
| `test_iof_35_para_remessa` | PTAX mudar drasticamente (cripto crash) | Baixo |
| `test_comparador_retorna_dataframe` | CoinGecko API mudar schema | Médio |
| `test_eFX_com_stablecoin_bloqueado` | BCB revogar BCB 561 | Baixo |

### Cenários de falha real
- Se CoinGecko ficar offline: `preco_stablecoin` retorna None → fallback PTAX + 0.5%
- Se Etherscan API mudar: `gas_fee_eth` retorna fallbacks fixos (10/20/50 gwei)
- Se BCB SGS cair: `ptax_venda` retorna None → fallback 5.0

---

## CONCLUSÃO

**3 falhas**, **2 ruins de explicabilidade**, **3 cenários de falsificabilidade mapeados**.

Débitos técnicos principais:
1. Margem de segurança para gas fee (2x)
2. Spread customizável por slider
3. Link para fonte do spread bancário
