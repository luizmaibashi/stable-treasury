# Proveniência dos dados

## O que alimenta o motor de risco

O histórico de peg de USDC e USDT vem da API pública da DefiLlama. A ingestão grava preços em Postgres e gera snapshots de risco a partir dessa mesma série. O cálculo de VaR e Expected Shortfall está em `src/depeg_risk.py` e a carga é reproduzível por `python -m scripts.seed_db`.

O backtest usa uma janela móvel de 90 dias, confiança de 97% e snapshots semanais. Ele serve para reconstruir como o motor teria medido a cauda de risco ao longo do tempo. Não é uma previsão de preço.

## Atualização e validade

No ambiente público, a atualização acontece na abertura do app quando o histórico está há mais de 24 horas sem atualização. O processo busca apenas o delta com uma sobreposição de um dia, usa lock consultivo no Postgres e mantém o último histórico válido quando a fonte falha.

Por isso, “atual” significa a última observação que foi persistida com sucesso. O watermark exibido na interface é a fonte de verdade para a data do dado mostrado. Não trate o gráfico como cotação garantida em tempo real.

## Como reproduzir localmente

```bash
docker compose up -d
python -m scripts.seed_db
python -m pytest -q
```

O seed é idempotente. Ele cria o schema, busca o histórico e grava preços e snapshots sem duplicar chaves já existentes. Detalhes de arquitetura e limites do método estão no [Deep Dive](../docs/DEEP_DIVE_DEPEG_ENGINE.md) e nos [ADRs](../docs/adr/).
