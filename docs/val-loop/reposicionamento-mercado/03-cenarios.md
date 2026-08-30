# Iteração 1 — cenários de negócio

## O Quê

Teste conceitual do pacote de decisão pré-pagamento, sem implementação.

| Cenário | Resultado esperado | Status | Implicação |
|---|---|---|---|
| Normal: fatura USD, duas cotações e política definida | Compara custo total e prazo; registra a razão da escolha. | Plausível | É o fluxo central. |
| Sem cotação comparável | Recusa ranking; entrega checklist de informação faltante. | Obrigatório | Evita inventar "melhor rota". |
| Regra regulatória incerta ou alterada | Marca revisão humana/jurídica; não bloqueia nem libera por conta própria. | Obrigatório | Evita aconselhamento jurídico travestido de automação. |
| Dado de preço, câmbio ou cotação vencido | Expõe horário e invalida a recomendação até atualização. | Obrigatório | Corrige a falha de proveniência achada na demo atual. |
| Empresa grande com TMS/ERP fragmentados | Aceita importação estruturada de dados; não promete integração em v1. | Plausível | Serve como diagnóstico, não substitui sistema corporativo. |
| Empresa sem pagamentos internacionais recorrentes | Não há recorrência nem economia suficiente. | Kill por segmento | Não é cliente inicial. |

## Critério operacional a provar depois

O pacote só cria valor se reduzir uma decisão real para uma janela compatível com vencimento, sem exigir entrada manual equivalente a preencher uma planilha completa.
