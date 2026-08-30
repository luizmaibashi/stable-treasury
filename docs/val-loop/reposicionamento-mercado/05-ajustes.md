# Iteração 1 — ajustes

## O Quê

Ajuste de direção: de comparador de trilhos orientado por stablecoin para pacote de decisão pré-pagamento orientado por evidência.

## Por Quê

O market scan confirmou dor, mas também mostrou que execução, custódia e liquidação são reguladas e competidas por provedores estabelecidos. A primeira versão precisa entregar valor sem atravessar essa fronteira.

## Como

| # | Ajuste | Por quê | Impacto |
|---|---|---|---|
| 1 | Stablecoin deixa de ser promessa central | Regulação e concorrência tornam a rota insuficiente como necessidade durável. | Preserva o Depeg Engine como análise condicional de risco. |
| 2 | Entrada passa a aceitar cotações recebidas | Sem integração bancária, o produto não pode prometer preço de mercado. | Resultado é decisão comparável, não "melhor cotação" inventada. |
| 3 | Saída passa a ser pacote de decisão rastreável | Dor observada é custo, atraso, exposição e documentação. | Cria artefato útil para aprovação e auditoria. |
| 4 | Compliance vira sinal de política e encaminhamento | Veredito jurídico automatizado gera risco de responsabilidade. | Mantém o produto fora de aconselhamento jurídico. |
| 5 | Segmento inicial é importador médio sem TMS completo | Enterprise é relevante, mas já tem TMS e custo alto de integração. | Wedge com menor dependência de integração; hipótese ainda precisa ser testada. |

## Próxima fronteira

Uma spec deve descrever o menor fluxo que produz um pacote de decisão com dados timestamped, cálculo reproduzível e ação humana explícita. Não deve incluir integração bancária, execução ou inferência jurídica.
