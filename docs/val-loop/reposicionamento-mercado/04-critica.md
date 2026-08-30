# Iteração 1 — crítica PAVC

## Advogado do diabo

1. **Vira uma planilha com interface bonita.** Se o usuário ainda coleta tudo manualmente, o custo de entrada anula o ganho.  
   **Mitigação exigida:** template mínimo de importação, cálculo auditável e um output que a planilha atual não produz: pacote de decisão reutilizável, com políticas e evidência temporal.

2. **Cruza a fronteira de responsabilidade regulatória.** Uma etiqueta "permitido" pode ser interpretada como parecer jurídico ou aprovação de compliance.  
   **Mitigação exigida:** linguagem de política e risco, não veredito legal; fonte, versão da regra e encaminhamento obrigatório para revisão humana em casos ambíguos.

3. **O alvo enterprise não troca nada por um dashboard isolado.** TMS, ERP e banco já são parte da operação e integração custa caro.  
   **Mitigação exigida:** começar por decisão pontual/semana crítica ou importador médio sem TMS, e provar redução mensurável de retrabalho antes de integrar.

## Cenários de borda que a futura spec deve cobrir

1. Fatura sem moeda, vencimento ou contraparte.
2. Cotação em moeda/unidade diferente, ou sem timestamp.
3. Valores extremos que excedem alçada de aprovação.
4. Duas pessoas revisando a mesma decisão com versões distintas da cotação.
5. Mudança de regra ou política depois da recomendação, antes da execução.

## Explicabilidade — pendente do usuário

Para passar este gate, o usuário deve explicar em palavras próprias: de onde vem cada dado, quem decide, o que o sistema calcula e qual ação fica deliberadamente fora do produto.
