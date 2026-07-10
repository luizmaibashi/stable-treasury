---
tipo: tarefa-simples
status: resolvido
criado: 2026-07-09
---

# Ticket 0005: Reconciliar Context Bridge Desatualizado

## Bloqueio
`brain/sessions/last_session_summary.md` datado 2026-07-04, descreve projeto com
4 módulos e 24 testes, backlog focado em "validar dashboard visualmente". Mas
ADRs 0003/0004/0005 (pivot pro Depeg Risk Engine + Postgres) são posteriores e
já estão implementados (`src/depeg_risk.py`, `src/db.py`, `src/repositorio.py`,
`src/ingestao.py`, `docker-compose.yml`, PAVC audit de 2026-07-05 já rodado).

## Resultado
**Estado real confirmado por leitura direta do código/docs (não da bridge):**
- Depeg Risk Engine implementado e testado (`test_depeg_risk.py`)
- Persistência Postgres via Docker implementada e testada (`test_repositorio.py`)
- PAVC audit já rodou 1x (2026-07-05), achou 2 dos 10 débitos técnicos (#9, #10)
- Backlog da bridge (validar dashboard, chave Etherscan, commit inicial) está
  obsoleto — pivot o substituiu
- Bridge precisa de novo `/session-bridge` refletindo o pós-pivot antes de
  qualquer trabalho novo, para não confundir sessões futuras
