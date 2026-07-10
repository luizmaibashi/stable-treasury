# ADR-0006: Deploy Público via Streamlit Community Cloud + Neon

**Data:** 2026-07-09
**Status:** Accepted
**Proposto por:** Luiz Maibashi (via wayfinder + grill-with-docs)

---

## 1. CONTEXTO (O Quê?)

Projeto reestruturado (docs/wayfinder/reestruturacao/SPEC_FINAL.md) reposiciona o
Depeg Risk Engine como protagonista da narrativa e exige link público — recrutador
precisa ver o dashboard rodando sem clonar repositório. ADR-0005 já estabeleceu
Postgres + SQLAlchemy como camada de persistência com dev/prod parity como requisito
explícito ("evitar surpresa de dialeto no deploy").

**Linguagem Ubíqua:** Neon (Postgres gerenciado), Cold start, DATABASE_URL — ver AGENTS.md.

**Restrição:** Streamlit Community Cloud não tem disco persistente (reset a cada
restart) — SQLite em produção perderia todo o histórico 2022→hoje já ingerido.

---

## 2. DECISÃO (Por Quê?)

- **Streamlit Community Cloud** hospeda o `app.py` publicamente, gratuito, conectado
  direto ao repositório GitHub.
- **Neon** (Postgres gerenciado, free tier) hospeda o banco de produção — mesma
  engine do Docker local, só troca o endereço via `DATABASE_URL`.
- Nenhuma linha de código muda: `src/db.py::get_engine()` já lê `DATABASE_URL` do
  ambiente (arquitetura do ADR-0005 previu exatamente este cenário).

**Razão Principal (ROI):**
> "Recrutador clica no link, vê o dashboard rodando com o backtest histórico real
> (evento SVB mar/2023) sem precisar clonar/instalar nada. Igualmente importante:
> o processo de configurar Neon + variável de ambiente em produção é, em si, o
> objetivo de aprendizado — entender cada peça de um deploy real, não só o código."

---

## 3. CONSEQUÊNCIAS

**Positivas:**
- Dev/prod parity do ADR-0005 se mantém (não diverge — se estende)
- Custo zero preservado
- Link público habilita avaliação por terceiros sem fricção de setup
- Aprendizado prático de deploy com banco gerenciado (habilidade de mercado real)

**Negativas:**
- Cold start: banco pausa após inatividade no free tier, primeira consulta pós-pausa
  demora alguns segundos a mais — aceito conscientemente (ticket 0004, wayfinder)
- Mais uma conta/serviço externo a manter (Neon), além do GitHub e Streamlit Cloud

---

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê foi rejeitada |
|-------|----------------------|
| SQLite em produção | Já rejeitada no ADR-0005 — Streamlit Cloud reseta disco, dado sumiria |
| Supabase | Funcionalmente equivalente a Neon pro nosso uso (só Postgres puro); Neon escolhido por cold start mais rápido |
| Manter só local (sem deploy público) | Não atende ao objetivo de portfolio (recrutador precisa de link, não repo pra clonar) |

---

## 5. IMPACTO ROI

- **Métrica de sucesso:** link público abre E gráfico de backtest histórico
  (evento SVB, mar/2023) aparece idêntico ao ambiente local
- **Timeline:** validar na mesma sessão da reestruturação de narrativa
- **Risco de regressão:** se Neon mudar termos do free tier ou pausar
  definitivamente por inatividade prolongada, reingestão via `src/ingestao.py`
  recompõe o histórico (idempotente, já testado)

---

## 6. LINKS RELACIONADOS

- `docs/adr/0005-persistencia-sqlalchemy-docker.md` (decisão que este ADR estende)
- `docs/adr/0003-pivot-depeg-risk-engine.md` (já apontava Supabase/Neon como caminho)
- `docs/wayfinder/reestruturacao/SPEC_FINAL.md` (origem desta reestruturação)
- `src/db.py`, `.env.example` (DATABASE_URL)
