# Spec-0004: Observabilidade do modo degradado

**Data:** 2026-08-30
**Status:** Implementada nesta sessão, sujeita a revisão e publicação pelo proprietário

## Objetivo

Expor, na mesma execução do Rail Comparator, quando uma fonte pública falha e o cálculo usa uma premissa de fallback. Isso torna o resultado auditável para quem usa a demonstração e reduz o tempo para identificar uma fonte indisponível.

## Escopo

Inclui Binance (order book USDT/BRL e USDC/BRL) e PolygonScan (gas da Polygon), os dois fallbacks observados no ambiente público. A interface deve mostrar o componente afetado e a premissa usada, sem expor a mensagem técnica da exceção.

Fora de escopo: retentativas, monitoramento externo, armazenamento de eventos, mudança dos valores de fallback ou bloqueio da simulação.

## Critérios de aceitação

1. Order book indisponível produz diagnóstico `Binance` com a indicação de slippage heurístico por volume.
2. Falha no PolygonScan produz diagnóstico `PolygonScan` com a indicação do perfil padrão de 50 gwei.
3. A tela alerta somente quando houver ao menos um fallback na execução.
4. Logs registram evento estruturado com fonte, componente e fallback usado.
5. `comparar_custos` preserva o retorno público atual (`polars.DataFrame`).

## Restrições e riscos

Não há credenciais ou dados de terceiros persistidos. O fallback continua fail-safe: a simulação é produzida, mas seu caráter degradado fica explícito. O risco de regressão é duplicar chamadas às fontes; a implementação deve reutilizar as respostas já coletadas na comparação.

## Dono da decisão

Luiz Maibashi aprovou a implementação em 2026-08-30.
