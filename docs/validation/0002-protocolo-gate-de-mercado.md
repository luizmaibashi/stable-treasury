# Protocolo 0002 — Gate de mercado com tesoureiro real

**Status:** pronto para recrutamento; sem execução de produto adicional
**Escopo:** entrevista moderada de descoberta do MVP de decisão pré-pagamento
**Depende de:** [Kill gate 0001](0001-kill-gate-contra-planilha.md)

## Decisão que este protocolo suporta

Decidir se vale repetir a validação com outros dois decisores do ICP. Não decide
por integração, IA, execução financeira ou lançamento comercial.

Uma conversa não valida mercado. Ela só pode revelar, de modo barato, se o
**pacote de decisão** melhora a revisão de uma fatura em relação a uma planilha
bem feita, ou se a diferença é irrelevante para quem aprova esse tipo de
pagamento.

## Hipótese falsificável

Para um gerente financeiro ou tesoureiro de importador B2B industrial médio que
participa de pagamentos internacionais, o dossiê torna mais clara a origem da
cotação, a exceção de política e o impacto no caixa do que sua forma usual de
revisar o mesmo caso.

Esta hipótese é refutada nesta rodada se o participante não apontar nenhuma
evidência decisória mais fácil de revisar no dossiê **e** não conseguir indicar
uma lacuna concreta, material e verificável que explique a ausência de valor.
Nesse caso, encerrar a direção; adicionar feature seria apenas especulação.

## Participante e proteção de dados

Recrutar **um** participante que satisfaça todos os critérios:

- gerente financeiro, tesoureiro ou aprovador que tenha participado de ao menos
  quatro pagamentos internacionais nos últimos três meses;
- atua em importador B2B/industrial brasileiro, ou em operação materialmente
  equivalente;
- usa planilha, ERP/TMS ou e-mails para consolidar a decisão antes do parceiro
  financeiro executar o pagamento.

Não pedir nomes de fornecedores, valores reais, planilhas corporativas,
credenciais, políticas internas ou informação de cliente. O participante opera
somente sobre os dois casos sintéticos fornecidos. Se desejar mostrar sua
planilha, deve ser uma cópia vazia ou inteiramente anonimizada; isso não é
requisito.

## Sessão única de 45 minutos

| Tempo | Atividade | Evidência gerada |
|---|---|---|
| 0–5 min | Confirmar papel, frequência e processo atual; sem apresentar o produto | elegibilidade e baseline narrado |
| 5–10 min | Mostrar o objetivo e o escopo negativo: organiza evidência, não executa nem aprova | entendimento do limite do MVP |
| 10–20 min | Caso A sintético em planilha bem feita: pedir uma decisão ou o que bloquearia a aprovação | tempo, perguntas e exceções percebidas |
| 20–30 min | Caso B, equivalente em complexidade, no dossiê StableTreasury | mesmas medidas, sem reexplicar o caso |
| 30–40 min | Comparação guiada e explicação em voz alta | clareza, rastreabilidade e lacunas materiais |
| 40–45 min | Pergunta de reutilização e encerramento | veredito e próximo experimento ou kill |

Os casos A e B devem alternar entre participantes posteriores para reduzir o
efeito de aprender o domínio no primeiro exercício. Nesta primeira sessão, o
tempo é sinal secundário: casos diferentes e novidade do artefato tornam uma
comparação numérica causal desonesta.

## Roteiro de perguntas

1. “O que você precisaria saber para aprovar, revisar ou recusar este pagamento?”
2. “Qual alternativa escolheria agora — ou o que impediria a decisão?”
3. “De onde vem a cotação, qual é a sua validade e qual exceção mudaria sua ação?”
4. “O que você ainda precisaria buscar fora desta tela/planilha?”
5. “Comparando os dois exercícios: em qual artefato foi mais simples justificar
   a decisão para um revisor? Por quê?”
6. “Em um próximo caso equivalente, você reutilizaria o dossiê antes de enviar a
   instrução ao parceiro? Sim, não ou apenas se X? O que é X?”

O moderador não explica onde está uma exceção, não defende o produto e não
converte uma crítica em pedido de feature durante a sessão.

## Ficha de observação

Registrar a sessão em uma página, preservando somente respostas anonimizadas.

| Medida | Planilha (A) | Dossiê (B) | Como interpretar |
|---|---:|---:|---|
| Tempo até declarar decisão/revisão | minutos | minutos | secundária; não usar como prova isolada |
| Perguntas bloqueantes de revisão | n e texto | n e texto | separar dúvida do caso de falta de evidência no artefato |
| Exceções percebidas | n e quais | n e quais | comparar com as exceções construídas no caso |
| Origem e validade da cotação explicadas corretamente | sim/não | sim/não | rastreabilidade mínima |
| Caixa/exposição ou política usados na justificativa | sim/não | sim/não | verifica que o dossiê não virou só uma tela bonita |
| Preferência justificada | — | texto literal curto | não aceitar “gostei” sem mecanismo |
| Reutilizaria no próximo caso equivalente | sim/não/condicional | condição literal | intenção é sinal, não adoção |

## Regra de decisão da primeira rodada

| Resultado observado | Decisão |
|---|---|
| O participante explica corretamente origem/validade e ao menos uma exceção no dossiê; aponta mecanismo concreto de clareza ou rastreabilidade superior; e considera reutilizá-lo sem exigir execução ou integração | **Sinal para replicar:** repetir com dois participantes independentes antes de alegar valor de mercado. Não ampliar o MVP. |
| Não percebe diferença útil frente à planilha e não identifica lacuna material verificável | **Kill:** interromper a direção de produto. Documentar o aprendizado; não adicionar integrações ou IA para tentar salvar a hipótese. |
| Percebe valor, mas falta uma evidência material específica para a decisão | **Diagnóstico, não GO:** registrar a lacuna como hipótese. Só depois de duas ocorrências independentes a mesma lacuna pode virar candidato a nova spec; ainda não é autorização de construir. |
| Participante fora do ICP, sessão interrompida ou caso não comparável | **Inválido:** não contar como evidência positiva ou negativa; recrutar novamente. |

Depois de três participantes válidos, consolidar sempre com `n=3`, respostas
literais anonimizadas e intervalo/limitação qualitativa. Só então é lícito dizer
que há evidência inicial de mercado; não é evidência de disposição a pagar ou
adoção recorrente.

## Crítica prévia (PAVC leve)

1. **Viés de cortesia:** o participante pode elogiar o protótipo. Mitigação:
   exigir mecanismo concreto, observar a tarefa antes da pergunta de preferência
   e tratar elogio sem mecanismo como neutro.
2. **Viés de novidade e ordem:** o segundo exercício parece mais rápido porque o
   caso já foi aprendido. Mitigação: casos equivalentes e alternância de ordem a
   partir da segunda entrevista; tempo não aprova sozinho.
3. **Falso ICP:** um consultor ou pessoa sem alçada pode achar a ideia boa sem
   sofrer a dor. Mitigação: screener de participação recente em pagamentos e
   classificação explícita de sessão inválida.

## Artefatos da rodada

- convite curto e screener de elegibilidade;
- planilha baseline e caso sintético A;
- caso sintético B no dossiê, com as mesmas classes de exceção;
- ficha de observação preenchida e veredito contra a tabela acima.

Nenhum dado de cliente deve ser persistido no repositório. O único registro
versionável é uma síntese anonimizada do veredito e das lacunas recorrentes.
