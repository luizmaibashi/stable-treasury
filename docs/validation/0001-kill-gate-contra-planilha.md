# Kill gate 0001 — Dossiê versus planilha bem feita

**Status:** pronto para validação de mesa
**Escopo:** MVP de decisão pré-pagamento; dados totalmente sintéticos.

## Pergunta que este gate responde

O dossiê torna uma decisão de pagamento mais verificável que uma planilha bem feita, sem inventar inteligência de mercado?

Ele **não** mede ainda disposição a pagar nem adoção. Sem usuário real, esse resultado seria uma alegação sem evidência. Este é somente o piso: provar que o produto entrega um artefato completo, reproduzível e seguro nos casos que promete cobrir.

## Baseline honesto

Uma planilha bem feita consegue reproduzir os cálculos. Ela não é o inimigo nem um benchmark fraco. O MVP só tem razão de existir se reduzir o trabalho de revisão ao concentrar, em uma página, dados de origem, horário, política, cálculo e exceções.

| Dimensão | Planilha bem feita | Dossiê StableTreasury | Critério mínimo |
|---|---|---|---|
| Menor custo total | Fórmula por linha | Ordenação determinística | Valores idênticos em todos os casos |
| Política | Fórmulas/células espalhadas | Parâmetros e alertas explícitos | 100% das exceções do caso são visíveis |
| Tempo e origem | Geralmente comentário ou aba auxiliar | Fonte e timestamp por cotação | Nenhuma cotação sem proveniência gera recomendação |
| Caixa e exposição | Cálculos adicionais | Exibidos por alternativa e caso | Nenhum caso de caixa/exposição crítica fica verde |
| Aprovação | Processo externo | Recomendação condicional, sem execução | Nunca afirmar legalidade ou executar pagamento |

## Cenários de mesa

| Caso | Contexto sintético | Resultado esperado | Falha que ele tenta impedir |
|---|---|---|---|
| A — escolha limpa | Caixa de R$ 800 mil; recebimentos USD 150 mil; pagamentos já previstos USD 40 mil; fatura USD 100 mil; duas cotações recentes e dentro dos limites | `PRONTO_PARA_APROVACAO`; Corretora Beta primeiro por custo total de R$ 521 mil; exposição USD +10 mil | Escolher por taxa nominal e ignorar tarifa, prazo ou fonte |
| B — cotação aparentemente barata, mas fora da política | Mesmo caso A, mas uma cotação possui prazo acima do máximo ou timestamp vencido | `REVISAR`, com código e parceiro responsáveis | Tratar proposta expirada/fora da política como menor custo “vencedor” |
| C — menor custo que quebra caixa | Mesmo caso A, mas caixa BRL declarado é insuficiente para a alternativa | `REVISAR` e `CAIXA_INSUFICIENTE` por alternativa | Aprovar por custo ignorando saldo de caixa pós-pagamento |

Os três mecanismos já estão cobertos em `tests/test_decisao_pre_pagamento.py` e no PAVC de 2026-08-29.

## Regra de aprovação do gate

O MVP passa no **gate técnico** se, nos três cenários:

1. O custo total e a ordenação forem reproduzíveis a partir das entradas declaradas.
2. Todo dado ausente, temporalmente inválido ou fora da política impedir recomendação incondicional.
3. Um revisor enxergar, em uma única tela, a fatura, duas alternativas, premissas, alertas e limite do produto.
4. Não houver qualquer integração, cotação de mercado, execução financeira, parecer jurídico ou dado real de cliente.

O MVP só passa no **gate de mercado** após um tesoureiro comparar o mesmo caso com sua planilha. Métricas: tempo até decisão, número de perguntas de revisão, exceções encontradas e intenção de reutilizar. Se o artefato não superar a planilha em pelo menos clareza/rastreabilidade de exceções, a direção deve ser interrompida.

O procedimento enxuto, os critérios de recrutamento e a regra de parada estão em
[`0002-protocolo-gate-de-mercado.md`](0002-protocolo-gate-de-mercado.md). A
primeira entrevista é apenas um sinal de descoberta; evidência inicial de mercado
exige três participantes válidos e independentes.

Enquanto entrevistas não forem parte da estratégia, a
[`0003-varredura-documental-mercado-e-concorrencia.md`](0003-varredura-documental-mercado-e-concorrencia.md)
é o gate secundário: ela pode sustentar ou matar a plausibilidade da tese, mas não
substitui evidência de uso nem autoriza declarar que o dossiê supera uma planilha.

## Resultado atual

**Gate técnico: aprovado.** A suíte integral aprovou 107 testes e o fluxo da tela foi exercitado com o cenário A.
**Gate de mercado: não aprovado.** Sem entrevistas, o gate documental 0003 falhou em comprovar uma lacuna vendável. O MVP fica preservado como demonstração técnica; não transformar esse resultado em integração ou escopo adicional.
