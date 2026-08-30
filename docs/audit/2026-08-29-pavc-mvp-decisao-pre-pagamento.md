# PAVC — MVP de decisão pré-pagamento

**Data:** 2026-08-29  
**Escopo:** `src/decisao_pre_pagamento.py` e a aba correspondente do dashboard.

## Advogado do Diabo

| Hipótese de falha | Mecanismo | Proteção entregue | Limite restante |
|---|---|---|---|
| Uma cotação antiga ou com relógio errado parece atual | Timestamp ausente, vencido ou no futuro | Sem timestamp: `INCOMPLETO`; vencido/futuro: `REVISAR` | A origem do horário é declarada, não autenticada pelo parceiro |
| A menor cotação cria uma falta de caixa | A comparação olha apenas taxa/tarifa | O dossiê calcula caixa pós-pagamento por alternativa e bloqueia quando negativo | Não projeta entradas e saídas intradiárias além do contexto informado |
| Uma regra interna é violada e vira recomendação | Política fica fora da planilha ou é lida informalmente | Custo, prazo e alçada são parâmetros explícitos; exceções produzem `REVISAR` | A plataforma não valida se a política cadastrada é a política corporativa vigente |

## Explicabilidade

1. O responsável financeiro registra fatura, fluxo previsto, política e cotações que já recebeu de parceiros autorizados.
2. O produto calcula custo total, prazo, caixa pós-pagamento e exposição líquida; mostra as premissas e os alertas que levaram ao estado.
3. O aprovador humano aceita ou recusa fora da plataforma; banco, corretora ou parceiro regulado executa o pagamento.
4. O produto não movimenta recursos, não custodia, não cria cotações, não substitui ERP/TMS e não emite parecer jurídico ou regulatório.

## Casos de borda verificados

| Caso | Resultado esperado | Cobertura |
|---|---|---|
| Menos de duas cotações | `INCOMPLETO`, sem recomendação | teste automatizado |
| Timestamp ausente ou sem timezone | `INCOMPLETO` ou erro explícito; nunca UTC implícito | teste automatizado |
| Cotação vencida ou futura | `REVISAR` com código de alerta | teste automatizado |
| Custo, prazo, alçada ou exposição fora da política | `REVISAR` | teste automatizado |
| Caixa insuficiente | `REVISAR` com impacto por alternativa | teste automatizado |

## Veredito

**Aprovado para demonstração e entrevistas de descoberta.** O motor é deliberadamente determinístico e fail-safe: uma informação ausente ou exceção não produz uma falsa recomendação. Ainda não é adequado para operação corporativa real sem autenticação, trilha persistente de aprovação, ingestão confiável de política e validação com usuários do segmento.
