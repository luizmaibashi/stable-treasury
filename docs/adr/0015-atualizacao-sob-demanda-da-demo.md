# ADR-0015: Atualização sob demanda da demo pública

**Data:** 2026-08-30
**Status:** Accepted
**Proposto por:** Luiz Maibashi

## 1. Contexto

A versão pública pretendida é uma demonstração técnica do Depeg Risk Engine, não um produto comercial. Deixar o histórico do Neon congelar torna a demonstração enganosa; mantê-lo por cron adicionaria infraestrutura e manutenção sem retorno para o portfólio.

O banco já preserva `peg_prices` e `risk_snapshots`; `src/ingestao.py` já é idempotente. O problema é atualizar o delta quando a demo volta a receber uma visita após inatividade.

## 2. Decisão

Na abertura do dashboard, atualizar apenas os ativos cujo último preço persistido tenha mais de 24 horas. A coleta começa um dia antes do watermark para tolerar atraso ou revisão da fonte; a idempotência elimina duplicação. Os snapshots são então recalculados.

Um advisory lock do Postgres impede duas sessões públicas de atualizar ao mesmo tempo. Banco vazio não faz backfill automático: o seed continua explícito. Falha de fonte conserva o último estado e a UI informa a data efetivamente persistida.

O engine usa `pool_pre_ping=True`: antes de reutilizar uma conexão, valida que ela ainda está viva. Isso evita que um socket SSL fechado pelo Neon após inatividade/reboot vire erro visível no dashboard.

**Razão de ROI:** uma visita posterior a semanas de inatividade recupera a utilidade da demo sem cron, worker ou custo operacional recorrente. O custo aceito é alguns segundos na primeira visita vencida.

## 3. Consequências

**Positivas:**

- Dados se recuperam sob demanda, sem rotina diária ou novo deploy.
- Sem duplicação de chamadas em acessos simultâneos no Neon.
- A data exibida torna a atualidade falsificável.

**Negativas:**

- A primeira visita após 24 h pode sofrer cold start e latência da DefiLlama.
- Cada checkout do pool executa uma verificação leve de conexão; custo aceito para evitar falha visível após cold start.
- "Atual" significa a última observação disponível nas fontes gratuitas, não garantia de cotação em tempo real.
- O backtest é recalculado para o ativo atualizado; para o porte do portfólio, a simplicidade supera a complexidade de snapshots incrementais.

## 4. Alternativas descartadas

| Opção | Por que foi rejeitada |
|---|---|
| Cron diário | Adiciona serviço, credencial e operação para uma demo acessada esporadicamente. |
| Backfill completo na visita | Latência e rate limit imprevisíveis; banco vazio deve exigir ação consciente. |
| Atualizar a cada recarga | Desperdiça quota das APIs e aumenta cold starts sem ganho informacional. |

## 5. Validação

- `src.atualizacao.atualizar_se_defasado` não chama fonte no TTL e chama somente o delta vencido.
- Uma fonte indisponível não remove nem substitui o histórico persistido.
- A aba Risco de Depeg mostra `ultima_data_preco` como watermark auditável.
- A suíte automatizada cobre TTL, delta, banco sem seed, falha de fonte e timezone ausente.

## 6. Referências

- `docs/spec/0003-atualizacao-sob-demanda.md`
- `docs/adr/0005-persistencia-sqlalchemy-docker.md`
- `docs/adr/0006-deploy-publico-streamlit-neon.md`
- `src/atualizacao.py`
