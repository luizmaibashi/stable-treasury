# Sessão 2026-07-04 — StableTreasury: Implantação completa

## Contexto
Planejamento e implementação do projeto StableTreasury (02_PORTFOLIO) — motor de decisão para fintechs compararem trilhos de pagamento B2B.

## O que foi feito

### 1. Planejamento e Definição de Escopo
- **Pesquisa de mercado**: mercado B2B stablecoin cresceu 733% YoY ($226B/ano), Brasil processa ~$6-8B/mês em crypto (90% stablecoins)
- **BCB 561 mapeada**: proíbe liquidação via stablecoin para eFX (abril/2026), mas não afeta tesouraria própria nem remessas não-eFX
- **IOF incluído como alíquota pública tabelada**: 6 tipos de operação, fonte: Decretos 6.306/2007 e 12.499/2025
- **Escopo delimitado**: sem assessoria jurídica, sem licenciamento CVM/BCB, sem tributação de renda

### 2. Artefatos de Documentação
- `AGENTS.md` — Linguagem Ubíqua do projeto (17 termos definidos)
- `docs/adr/0001-fontes-de-dados.md` — CoinGecko + Etherscan + BCB SGS (custo zero)
- `docs/adr/0002-arquitetura-streamlit-modulos.md` — Streamlit + 5 módulos Python
- `docs/audit/pavc_audit.md` — 3 falhas, 2 explicabilidade ruim, 3 falsificabilidade mapeadas
- `data/raw/iof_aliquotas.yaml` — 6 alíquotas IOF com referência ao decreto

### 3. Código Entregue

| Módulo | Arquivo | O que faz |
|--------|---------|-----------|
| IOF Tabela | `src/iof_tabela.py` | Carrega alíquotas do YAML, cache singleton |
| Coletor Preços | `src/coletor_precos.py` | Wrappers CoinGecko (USDT, ETH, MATIC), Etherscan/PolygonScan (gas), BCB SGS (PTAX) com fallbacks |
| Rail Comparator | `src/comparador.py` | Compara custo total: Wire / PIX / USDT ERC-20 / USDT Polygon / USDC ERC-20 / USDC Polygon |
| Compliance Filter | `src/compliance.py` | Valida BCB 561 (stablecoin eFX), BCB 520 (KYC), BCB 521 (>R$500k) |
| Liquidity Optimizer | `src/otimizador.py` | Heurística de alocação BRL/USDT/USD com detecção de exportador |
| Dashboard | `app.py` | Streamlit com 4 tabs (Rail, Compliance, Liquidity, Config) |
| Testes | `tests/` (4 suites) | 24 testes, todos passando |

### 4. Validação com Dados Reais

**PTAX real (BCB SGS):** R$ 5.1711  
**USDT/BRL real (CoinGecko):** R$ 5.18  

**Resultado Rail Comparator (R$ 50k, remessa 3.5% IOF):**

| Trilho | Custo Total | % da Fatura |
|--------|------------|-------------|
| PIX | R$ 0,00 | 0,000% |
| USDT (Polygon) | R$ 0,03 | 0,000% |
| USDC (Polygon) | R$ 0,03 | 0,000% |
| USDT (ERC-20) | R$ 12,03 | 0,024% |
| USDC (ERC-20) | R$ 12,03 | 0,024% |
| Wire (SWIFT) | R$ 3.129,28 | 6,259% |

**Economia potencial: R$ 3.129,25 (99,99%) vs. Wire.**

### 5. Correções em Campo
- CoinGecko rate limit (429) → fallbacks implementados
- MATIC rebranded para POL → fallback $0.50
- Etherscan sem API key → fallback 20 gwei
- BCB SGS mudou API (requer dataInicial) → corrigido com parâmetros de data
- Streamlit `use_container_width` deprecado → migrado para `width="stretch"`

### 6. Pendências
- Streamlit rodando em `http://localhost:8501` (precisa revisão visual do usuário)
- Gas fee sem API key usa fallback fixo (ideal: obter chave Etherscan gratuita)
- MATIC/POL price sem ID CoinGecko correto (fallback $0.50)
- Spread bancário fixo em 2.5% (ideal: slider customizável no dashboard)
