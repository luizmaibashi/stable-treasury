# ADR-0001: Fontes de dados gratuitas (CoinGecko + Etherscan + BCB SGS)

**Data**: 2026-07-04
**Status**: Accepted (estendido pelo ADR-0003 §5b — DefiLlama para série histórica de peg)
**Contexto**: StableTreasury

---

## 1. CONTEXTO (O QUÊ?)

O StableTreasury precisa de 3 tipos de dado externo para funcionar sem custo operacional:
- Preço de stablecoins (USDT, USDC) em BRL
- Gas fee estimado para transações on-chain (Ethereum, Polygon)
- Taxa de câmbio oficial BRL/USD (referência BCB)

**Restrições técnicas:**
- **Custo zero obrigatório**: portfolio showcase, sem orçamento para APIs pagas
- **Dados reais, não mock**: a credibilidade do comparador depende de preços vivos
- **Latência tolerável**: dados podem ser de até 5 min atrás (não é trading)
- **Sem chave de API obrigatória**: mas com fallback se a chave não existir

**Métricas:**
- Preço stablecoin: erro < 0.5% vs. referência de mercado
- Gas fee: erro < 10% (estimativa, não executado)
- Câmbio oficial: spread < 0.1% vs. PTAX

---

## 2. DECISÃO (POR QUÊ?)

**O que escolhemos:**
- **CoinGecko API** (`/simple/price`): preço USDT/USDC em BRL — gratuita, sem taxa, amplamente usada
- **Etherscan API** (`/api?module=gastracker&action=gasoracle`): gas fee Ethereum estimado — gratuita com rate limit 5 calls/sec
- **PolygonScan API** (idem): gas fee Polygon — mesma lógica da Etherscan
- **BCB SGS API** (`https://api.bcb.gov.br/dados/serie/bcdata.sgs.10813/dados`): câmbio BRL/USD (SGS 10813 = PTAX venda) — gratuita, sem taxa, sem chave

**ROI:**
> "Se NÃO fizermos: custo ~$200/mês com APIs pagas (CoinMarketCap, Kaiko, Bloomberg) para dados que precisamos apenas 1-2x/dia."
> "Se fizermos: economia de $200/mês com latência de < 5 min e mais de 99% de disponibilidade histórica."

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- Custo operacional zero
- Dados públicos e verificáveis (reprodutibilidade acadêmica)
- Sem dependência de vendor lock-in (qualquer API gratuita substitutível)

**Negativas:**
- Rate limits podem bloquear em horário de pico (CoinGecko: 10-30 req/min)
- Etherscan não dá gas fee de L2s (Arbitrum, Optimism)
- BCB SGS não tem cotação intradiária (só PTAX de fechamento)

**Timeline:**
- Implementação: 1 hora (3 wrappers de API)
- Benefit realization: imediata

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| CoinMarketCap API | Dados mais rápidos | ❌ Chave de API paga após 10k calls/mês |
| Binance API (livestream) | Preço real-time | ❌ Requer WebSocket + complexidade extra |
| AwesomeAPI (câmbio) | PTAX em tempo real | ❌ Confiabilidade menor que BCB SGS oficial |
| Preços mockados | Simples | ❌ Projeto perde credibilidade real |

---

## 5. IMPACTO & VALIDAÇÃO

**Métrica de sucesso:**
- Wrappers em `src/coletor_precos.py` retornam preço/câmbio reais das APIs, com fallback quando fora do ar
- Cobertura de comportamento: `tests/test_comparador.py` e `tests/test_depeg_risk.py` exercitam o
  fluxo com dados reais dessas fontes (não há suíte dedicada `test_coletor_precos.py`)

**Monitoramento (fallbacks implementados em `src/coletor_precos.py`):**
- CoinGecko fora do ar (HTTP 429): `preco_stablecoin` retorna None → comparador usa PTAX + spread
- Etherscan/PolygonScan sem chave: gas fee cai em fallback fixo de gwei
- BCB SGS fora do ar: `ptax_venda` retorna None → fallback 5.0

---

## 6. REFERÊNCIAS

- [CoinGecko API Docs](https://www.coingecko.com/en/api)
- [Etherscan API Docs](https://docs.etherscan.io/api-endpoints/gas-tracker)
- [BCB SGS API](https://dadosabertos.bcb.gov.br/dataset/10813-taxa-de-cambio-todos-os-boletins-diarios)
