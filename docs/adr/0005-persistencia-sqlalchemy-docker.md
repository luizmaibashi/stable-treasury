# ADR-0005: Persistência com SQLAlchemy + Postgres em Docker

**Data**: 2026-07-05
**Status**: Accepted
**Contexto**: StableTreasury — implementa a infra de persistência prometida no ADR-0003

---

## 1. CONTEXTO (O QUÊ?)

O ADR-0003 decidiu sair do estado 100% stateless para persistir histórico (débito técnico #6).
Restavam decisões de implementação: qual engine local, como versionar schema, como manter os
testes rápidos sem depender de banco externo, e como carregar o histórico.

**Restrições:**
- Custo zero mantido
- Usuário quer aprender Docker a fundo (essencial no mercado de dados/IA) — decisão explícita 2026-07-05
- Testes não podem depender de rede/conta externa (regra de agilidade)
- Dev e prod devem ter o mesmo motor de banco (evitar surpresa de dialeto no deploy)

---

## 2. DECISÃO (POR QUÊ?)

- **Postgres 16 em Docker** (`docker-compose.yml`) para desenvolvimento local — não instala Postgres
  na máquina, sobe com `docker compose up -d`, dados persistem em volume nomeado (`pgdata`).
- **SQLAlchemy 2.0 Core como fonte ÚNICA do schema** (`src/db.py::metadata`) — as mesmas tabelas
  são criadas via `create_all` tanto no SQLite em memória (testes) quanto no Postgres (dev/prod).
  Evita a dupla fonte de verdade que um `.sql` cru + modelos ORM causariam.
- **Repositório agnóstico de dialeto** (`src/repositorio.py`) — idempotência por leitura-e-filtro
  (não `ON CONFLICT` dialeto-específico), e normalização de timezone (UTC-naive na escrita,
  UTC-aware na leitura) para SQLite e Postgres se comportarem idênticos no Python.
- **Duas tabelas** (`peg_prices` bruto imutável, `risk_snapshots` derivado recalculável) —
  separação por ciclo de vida do dado (preço nunca muda; risco é recalculado se o modelo muda).
- **Ingestão paginada** (`src/ingestao.py`) — DefiLlama rejeita span > ~500 dias/chamada, então o
  backfill 2022→hoje é quebrado em janelas de 450 dias; `salvar_precos` idempotente cobre a
  sobreposição. Backtest rolante (`gerar_snapshots_risco_historico`) reconstrói a série de ES.

**Razão Principal (ROI):**
> "Postgres em Docker dá dev/prod parity real (mesmo motor local e no deploy) e ensina a ferramenta
> que o mercado de dados/IA exige. SQLAlchemy como fonte única mantém testes rápidos (SQLite em
> memória) sem divergir do schema de produção. O deploy do Módulo 6 (Supabase) recebe o mesmo código."

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- Projeto deixa de ser stateless — série histórica de preço e risco persistida (débito #6 fechado)
- Backtest possível: ES rolante sobre 2022→hoje; pico do USDC cai em mar/2023 (evento SVB),
  reproduzindo o ES de calibração do ADR-0004 (1,76%) de forma independente
- `docker compose up` provisiona ambiente idêntico em qualquer máquina (reprodutibilidade)
- Testes rodam em SQLite in-memory (rápidos, sem rede) mas o mesmo código roda em Postgres

**Negativas / limitações:**
- Docker Desktop exige virtualização + WSL2 no Windows (fricção de setup inicial, resolvida)
- SQLite (teste) não guarda timezone — resolvido com normalização, mas é uma pegadinha de dialeto
  que exige atenção se novas colunas temporais forem adicionadas
- Backfill depende da DefiLlama; sem ela, banco não popula (mas dado já persistido sobrevive)

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê rejeitada |
|-------|----------------------|
| SQLite em produção | Streamlit Cloud reseta disco a cada restart — dado sumiria; sem dev/prod parity com Supabase |
| `.sql` migration cru como fonte do schema | Dupla fonte de verdade com os modelos → drift; para este porte, metadata + create_all (Alembic quando evoluir) é mais seguro |
| `ON CONFLICT` para idempotência | Sintaxe diverge entre SQLite e Postgres; leitura-e-filtro é agnóstica |
| Postgres instalado direto na máquina (sem Docker) | Não ensina Docker (objetivo do usuário) e não dá reprodutibilidade de `compose up` |

---

## 5. IMPACTO & VALIDAÇÃO

**Métrica de sucesso (atingida):**
- `docker compose up -d` sobe Postgres 16 healthy; `init_schema` cria as tabelas
- Backfill real: 1643 linhas USDC + 1640 USDT (2022→2026) no Postgres
- 223 snapshots de risco/ativo; pico USDC em 2023-03-19 (janela SVB) = ES 0,0176
- Testes: `test_repositorio.py` (4) e `test_ingestao.py` (3) verdes em SQLite in-memory;
  mesmo repositório validado por smoke test contra Postgres real

**Risco de regressão:** schema muda → `metadata` é a fonte única, atualizar lá; adicionar coluna
temporal exige repetir a normalização de timezone do repositório.

---

## 6. LINKS RELACIONADOS

- `docs/adr/0003-pivot-depeg-risk-engine.md` (decidiu persistir), `docs/adr/0004-...` (parâmetros do risco)
- `docker-compose.yml`, `src/db.py`, `src/repositorio.py`, `src/ingestao.py`
- `tests/test_repositorio.py`, `tests/test_ingestao.py`
- `.env.example` (DATABASE_URL; `.env` real fica fora do git)