---
tipo: grilling
status: resolvido
criado: 2026-07-09
---

# Ticket 0004: Precisa Estar Publicamente Deployado?

## Bloqueio
Dashboard hoje só roda local (`streamlit run app.py`, localhost:8501). Se objetivo
é portfolio pra recrutador (ticket 0001-a), link vivo (Streamlit Community Cloud,
gratuito) muda completamente a experiência de avaliação — recrutador clica e vê
rodando, não precisa clonar+rodar. Se objetivo é estudo técnico interno (0001-b),
deploy é custo sem retorno.

Também depende de infra: projeto usa Postgres via Docker (ADR-0005) para dev/prod
parity — precisa decidir se o deploy público usa Postgres gerenciado (custo) ou
aceita SQLite em produção (quebra a paridade que o ADR-0005 buscou).

## Resultado
**Sim, Streamlit Community Cloud (gratuito) + Neon (Postgres gerenciado, free tier).**
Correção pós Blind Spot Pass: SQLite em produção foi cogitado inicialmente, mas
ADR-0005 já tinha rejeitado essa opção explicitamente ("Streamlit Cloud reseta disco
a cada restart — dado sumiria"). ADR-0003 já apontava Supabase/Neon como caminho.
Decisão final: Neon, mantendo dev/prod parity do ADR-0005 (Postgres nos dois lados,
só muda o endereço via `DATABASE_URL`). Não diverge do ADR-0005 — reforça ele.
