# PAVC Audit — StableTreasury

**Data**: 2026-07-04 (auditoria original, Rail Comparator/Compliance) — **atualizado 2026-07-05** (Depeg Risk Engine + Persistência, pós ADR-0003/0004/0005)
**Framework**: Maibashi PAVC (Advogado do Diabo, Explicabilidade, Falsificabilidade)

---

## PARTE 1 — Auditoria original (Rail Comparator / Compliance Filter, 2026-07-04)

## 1. ADVOGADO DO DIABO

### Falha 1: Gas fee estimado não reflete execução real
- **Crítica**: Gas fee da Etherscan é uma estimativa do próximo bloco, não o custo real de uma transação USDT ERC-20 (que pode ser 2-3x maior com dados de contrato)
- **Impacto**: Subestimação de custo dos trilhos on-chain em até 3x
- **Mitigação**: Adicionar margem de segurança de 2x no gas fee estimado — **ainda não implementada**

### Falha 2: Spread bancário é fixo (2.5%), mas varia por banco e volume
- **Crítica**: Bradesco, Itaú, Santander têm spreads diferentes; clientes corporativos negociam spreads melhores
- **Impacto**: O comparador superestima custo Wire para grandes volumes
- **Mitigação**: Adicionar slider de spread customizável no dashboard — **ainda não implementada**

### Falha 3: IOF sobre stablecoin é tratado como 0%, mas há contencioso
- **Crítica**: IN RFB 1888/2019 diz que cripto não é moeda, mas RFB já autuou empresas que usam stablecoin como moeda de câmbio
- **Impacto**: Risco fiscal não modelado
- **Mitigação**: Nota no README — **pendente (README ainda não escrito, ver Módulo 6)**

## 2. EXPLICABILIDADE

### Bom
- Cálculo de custo por trilho é determinístico e rastreável
- IOF vem de tabela YAML pública com referência ao decreto
- Compliance Filter expõe quais resoluções foram aplicadas

### Ruim
- Preço do gas fee não mostra breakdown (gwei × gas units × preço ETH)
- Liquidity Optimizer não explica heurística de alocação (50/30/20) — **RESOLVIDO em 2026-07-05, ver Parte 2**
- Spread bancário não tem trace de fonte (B3/FEBRABAN não linkado)

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

## PARTE 2 — Auditoria do pivot: Depeg Risk Engine + Persistência (2026-07-05)

## 1. ADVOGADO DO DIABO

### Falha 1: Risco medido só sobre USDC, aplicado ao total em stablecoin
- **Crítica**: `avaliar_risco_atual` avalia só `usd-coin`; USDT (perfil de reserva/attestation distinto) usa o mesmo teto
- **Impacto**: Se USDT descolar do peg sem USDC descolar, o teto de alocação não reage
- **Mitigação**: Documentado em `app.py` e AGENTS.md débito #7. **Não corrigido** — ideal é teto ponderado pela composição real da carteira

### Falha 2: Granularidade diária subestima o mínimo intra-dia real
- **Crítica**: DefiLlama `period=1d` amostra 1 ponto/dia; o mínimo real do USDC-SVB foi $0,8767 (hourly), a série diária registra ~$0,96
- **Impacto**: VaR/ES calculado sobre dado diário é sistematicamente mais otimista que o risco real intra-dia
- **Mitigação**: Documentado (AGENTS.md #8). **Não corrigido** — mitigável usando `period=1h` em janelas de stress

### Falha 3: Confiança 97% e janela 90d são calibração com apenas 2 âncoras históricas
- **Crítica**: Os cortes de faixa (5%/30%) foram calibrados com só 2 eventos reais (USDC-SVB, UST) — amostra pequena pra generalizar fronteiras
- **Impacto**: Um 3º evento histórico com perfil intermediário poderia exigir recalibração das faixas
- **Mitigação**: Documentado no ADR-0004 como limitação conhecida; testes de classificação travam a calibração atual contra mudança acidental

## 2. EXPLICABILIDADE

### Bom
- Todo parâmetro do motor de risco (confiança, janela, faixas) tem fonte documentada no ADR-0004 (Basel FRTB, cadência de attestation, ES real de crise)
- Backtest reproduziu de forma independente o ES de calibração (pico USDC em 2023-03-19 = 0,0176, igual à âncora do ADR-0004) — evidência de que a lógica é internamente consistente, não coincidência de calibração circular
- Injeção de dependência (`otimizador.py` recebe risco pronto) mantém a função de alocação pura e testável sem rede

### Assunção oculta identificada nesta auditoria
- `_utc_naive`/`_com_utc` (repositório) assumem implicitamente que qualquer `datetime` sem timezone já está em UTC — não há validação. Se algum código futuro passar um datetime naive em horário local (não UTC), o dado é persistido silenciosamente errado. **Documentado agora nesta auditoria; sem enforcement automático.**

## 3. FALSIFICABILIDADE — 5 cenários testados contra o código real (não hipotéticos)

| Cenário | Teste executado | Resultado antes | Ação |
|---|---|---|---|
| **1. Vazio** | `var_es_historico(np.array([]))` | 🔴 `IndexError` cru | **Corrigido**: agora `ValueError` claro (`tests/test_depeg_risk.py::test_var_es_historico_com_array_vazio_levanta_erro_claro`) |
| **2. Extremo** | `confianca` fora de [0,1] (1.5, -0.1) | ⚠️ Aceito silenciosamente (clampa pro mesmo resultado de 1.0/0.0) | Não corrigido — baixo risco (função interna, nunca exposta a input de usuário direto); registrado como known-limitation |
| **3. Corrupto** | `salvar_precos` com `price=None` e `price=NaN` | ✅ Passou — schema (`NOT NULL`) rejeita ambos com `IntegrityError`, sem corromper a tabela | Nenhuma ação necessária (proteção de schema funcionando como esperado) |
| **4. Concorrência** | 2+ escritas simultâneas do mesmo ponto (`peg_prices`) | 🔴 `IntegrityError` não tratado (TOCTOU: SELECT verifica existência, INSERT sem atomicidade) | **Corrigido**: savepoint por linha + `except IntegrityError` → idempotente. Verificado contra Postgres real do container: 5 tentativas × 5 threads concorrentes, sempre 1 sucesso + N no-ops, zero exceção |
| **5. Temporal** | `datetime` naive (sem tzinfo) salvo e lido | ✅ Aceito e devolvido como UTC-aware — comportamento é o documentado (assume naive=UTC), mas sem validação (ver Explicabilidade acima) | Nenhuma correção nesta rodada — risco baixo (só o próprio código do projeto grava nessas tabelas) |

**Nota de rigor**: o cenário 4 foi inicialmente testado com threads sobre SQLite (`StaticPool`), que expôs um problema *diferente* do bug real — limitação do driver `sqlite3` puro-Python em não ser thread-safe para conexão única compartilhada (`InterfaceError`, `no such savepoint`). O teste automatizado foi ajustado para simular a colisão via lote (não via threading em SQLite), e o fix foi validado separadamente à mão contra o Postgres real do container (onde a concorrência de fato importa, via pool de conexões). Documentado para não confundir "limitação da ferramenta de teste" com "bug do código".

---

## CONCLUSÃO GERAL

**Parte 1 (original)**: 3 falhas, nenhuma corrigida ainda (gas fee margem, spread slider, README com nota fiscal) — mantidas como débito conhecido, fora do escopo do pivot atual.

**Parte 2 (pivot)**: 3 falhas de advogado do diabo (2 documentadas como débito, 1 é limitação de amostra pequena), 1 assunção oculta documentada, **2 bugs reais corrigidos** via falsificabilidade agressiva (array vazio, race condition) — ambos com teste de regressão. 44/44 testes verdes pós-correção.

**Débitos técnicos consolidados**: ver `AGENTS.md` #1-8 do projeto.