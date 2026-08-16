# Proveniência de Dados — stable-treasury

**Data de auditoria:** 2026-08-15  
**Gate CRISP-DM:** ✅ Verificação de Origem iniciada

---

## Fonte

### Histórico de Preços
- **Sistema de origem:** DefiLlama (interface JSON pública)
- **IDs de moeda:** `usd-coin` (USDC), `tether` (USDT) via CoinGecko
- **Período:** 2022-01-01 00:00 UTC até presente
- **Frequência:** Diária (1 ponto/dia)
- **Endpoint:** Paginação por chunck de 450 dias máx. (restrição da API)
- **Reprodutibilidade:** ✅ Determinístico via `src/ingestao.py::backfill_completo()`

### Snapshots de Risco (Backtest)
- **Origem:** Série de preços persistida (acima) + cálculo local
- **Cálculo:** VaR/ES via janela móvel (90 dias, confiança 97%, passo 7 dias)
- **Fórmula:** `src/depeg_risk.py::var_es_historico()`
- **Persistência:** Postgres local (`stable_treasury_db`, schema auto-gerado)

---

## Timestamp da Fonte

**Confirmado via evidência de repositório** (`brain/sessions/last_session_summary.md`, banco Neon de produção) — não inventado, achado documentado:

- **Última ingestão confirmada:** 2026-07-16 — `python -m scripts.seed_db` rodou contra `DATABASE_URL` do Neon (produção)
- **Volume confirmado por leitura:** 1.654 preços USDC + 1.651 USDT, 225+224 snapshots de risco
- **Validação de conteúdo:** pico de ES 1,763% (SVB, mar/2023) presente no banco de produção — confirma que o backfill 2022→2026 chegou até o evento correto
- **Idade do dado nesta auditoria (2026-08-15):** ~30 dias sem re-ingestão desde a última run confirmada

**⚠️ Gap real, não fabricado:** não há confirmação se o `seed_db.py` rodou de novo entre 07-16 e hoje (08-15). Histórico de preço é backtest (não precisa ser "hoje"), mas se o dashboard afirma "risco atual" em vez de "risco até 16/jul", a alegação está desatualizada em ~1 mês. Isso é exatamente o padrão de risco que motivou este gate (post do LinkedIn) — só que numa escala bem menor (30 dias, não "meses parado").

---

## Rastro de Extração

### Script de Seed (Ponto de Entrada Único)
```bash
python -m scripts.seed_db
# ou
python scripts/seed_db.py
```

**Sequência:**
1. `scripts.seed_db::main()` → conecta ao `DATABASE_URL` (ou `docker-compose`)
2. `src.db::init_schema()` → cria/respeita schema existente (idempotente)
3. `src.ingestao::backfill_completo()` → itera sobre `STABLECOINS_PADRAO`
4. Para cada moeda:
   - `ingerir_historico()` → chunca período 2022→hoje em períodos de 450d
   - `depeg_risk.py::historico_pontos_peg()` → GET DefiLlama, parse JSON
   - `repositorio.py::salvar_precos()` → INSERT/UPDATE idempotente no Postgres
5. `gerar_snapshots_risco_historico()` → backtest com janela 90d, passo 7d
6. Snapshots salvos em tabela `risk_snapshots` (Postgres)

### Reprodução Passo a Passo
```bash
# 1. Garantir banco local
docker compose up -d

# 2. Rodar seed (idempotente; só insere o que não existe)
python -m scripts.seed_db

# 3. Verificar dados no banco
psql -h localhost -U treasury -d stable_treasury \
  -c "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM precos WHERE coin_id = 'usd-coin';"
```

**Validação de integridade:**
- Tabelas: `precos`, `risk_snapshots` (ambas em Postgres)
- Índices: `(coin_id, timestamp)` (único em preços, garante idempotência)

---

## Status de Validação

| Ponto de Checagem | Status | Observação |
|---|---|---|
| **Fonte documentada** | ✅ | DefiLlama + CoinGecko, período 2022→presente |
| **Endpoint público?** | ✅ | SIM, sem autenticação (rate limit ~10 req/s) |
| **Recuperabilidade** | ✅ | Script determinístico, idempotente |
| **Timestamp origem** | ✅ CONFIRMADO | 2026-07-16, banco Neon de produção (não local) |
| **Dados no banco?** | ✅ CONFIRMADO | 1.654+1.651 preços, 225+224 snapshots, validado por leitura |
| **Atualização recente?** | ⚠️ 30 DIAS DESATUALIZADO | Sem re-ingestão confirmada desde 07-16. Aceitável para backtest histórico; problemático se dashboard afirmar "risco atual" |

---

## Achado Central Desta Auditoria

**O Deep Dive que este gate ia bloquear já foi executado — 2026-07-14, com estes mesmos dados.** `docs/DEEP_DIVE_DEPEG_ENGINE.md` responde as 5 perguntas do checklist com números computados sobre a série real (não estimados). O bridge da base (`brain/sessions/frentes/stable_treasury.md`) descrevia o projeto como "pausado, aguardando Deep Dive" — desatualizado desde 07-16, quando o projeto foi **publicado** (Neon + Streamlit Cloud, repo público).

## Próximo Passo

1. Corrigir `brain/sessions/frentes/stable_treasury.md` + `INDEX.md` — status real é "publicado", não "pausado aguardando Deep Dive"
2. Decidir se vale rodar `seed_db.py` de novo (dado 30 dias desatualizado) antes de qualquer nova alegação de "risco atual" no dashboard
3. Pendência de higiene aberta: senha do Neon exposta em texto no chat de 07-16, nunca resetada

