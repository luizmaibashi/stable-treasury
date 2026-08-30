# Spec 0003: Atualização sob demanda da demo pública

**Status:** Aprovada para implementação local em 2026-08-30
**Dono da decisão e aprovação final:** Luiz Maibashi

## Objetivo

Manter a demo técnica útil quando for aberta após inatividade, buscando somente o
histórico ausente e recalculando o risco, sem agendamento, deploy recorrente ou
promessa comercial de disponibilidade.

## Escopo

- Na abertura, avaliar a idade do último preço persistido para USDC e USDT.
- Após 24 horas, ingerir somente o intervalo ausente, com uma sobreposição de um dia,
  e recalcular os snapshots dos ativos atualizados.
- Exibir a data do último dado e falhar de forma segura: manter e identificar o último
  estado válido se a fonte ou banco falhar.
- Coordenar atualizações concorrentes na produção Postgres para não duplicar chamadas.

## Fora de escopo

- Backfill automático de banco vazio; ele continua sendo operação explícita de seed.
- Cron, worker, fila, API REST, reingestão contínua ou alteração de credenciais.
- Push, deploy ou sincronização do repositório público.

## Critérios de aceitação

1. Série sem dado ou com até 24 horas não chama a ingestão.
2. Série com mais de 24 horas chama a ingestão apenas a partir do último ponto menos
   um dia e recalcula o snapshot do ativo.
3. Falha na atualização não impede a visualização do último histórico persistido.
4. Duas execuções públicas concorrentes não atualizam simultaneamente.
5. Testes unitários cobrem série ausente, recente, defasada e falha.

## Riscos e restrições

- O primeiro acesso após o TTL pode sofrer cold start do Neon e latência das APIs.
- APIs públicas podem atrasar ou falhar; "atual" significa última observação disponível
  na fonte, não cotação garantida em tempo real.
- Não há PII ou credencial no escopo. `DATABASE_URL` continua somente nos Secrets do
  Streamlit e no ambiente local do proprietário.
