# Spec 0001 — MVP: Pacote de Decisão Pré-Pagamento

**Status:** Aceita e implementada como MVP demonstrável  
**Data:** 2026-08-29  
**Dono da decisão e aprovação:** Luiz Maibashi  
**ADR:** `docs/adr/0013-reposicionamento-para-decisao-pre-pagamento.md`

**Evidência de implementação (2026-08-29):** `src/decisao_pre_pagamento.py`, aba “Decisão pré-pagamento” em `app.py`, 13 testes específicos e suíte integral com 107 testes aprovados. O PAVC está em [`docs/audit/2026-08-29-pavc-mvp-decisao-pre-pagamento.md`](../audit/2026-08-29-pavc-mvp-decisao-pre-pagamento.md).

## 1. Objetivo

Permitir que o gerente financeiro de um importador industrial brasileiro de porte médio compare duas ou mais cotações recebidas para uma fatura internacional e gere, em até cinco minutos, uma decisão rastreável de pagamento.

O valor não é executar câmbio: é tornar explícitos custo total, prazo, efeito sobre caixa, exposição e violação de política antes de a empresa instruir seu banco, corretora ou parceiro autorizado.

## 2. Usuário e evento de uso

**Usuário inicial:** gerente financeiro de importador B2B/industrial, com 4–20 pagamentos internacionais por mês e faturas típicas entre R$100 mil e R$2 milhões.

**Evento:** uma fatura de fornecedor em USD chega com vencimento próximo; o usuário possui ao menos duas cotações de parceiros autorizados e precisa justificar qual rota será aprovada.

## 3. Escopo do MVP

### Incluído

1. Formulário de fatura: identificador, fornecedor, valor em USD, vencimento e tipo de operação.
2. Registro de duas ou mais cotações: parceiro, taxa USD/BRL, tarifa em BRL, prazo de liquidação, horário da cotação e observação/fonte declarada.
3. Dados mínimos de contexto: caixa BRL disponível, recebimentos USD em 30 dias e pagamentos USD em 30 dias.
4. Política configurável por decisão: custo máximo (%), prazo máximo (dias) e alçada de valor em BRL.
5. Comparação reproduzível de custo total, prazo e exposição líquida em USD.
6. Pacote de decisão em tela, com: alternativas ordenadas, premissas, timestamp, campos ausentes, alertas de política e recomendação condicionada.
7. Estado explícito da decisão: `INCOMPLETO`, `REVISAR` ou `PRONTO_PARA_APROVACAO`.

### Fora de escopo

- Executar pagamento, câmbio, custódia ou transferir ativos.
- Conectar ERP, banco, corretora, API de cotação ou API de compliance.
- Gerar preço de mercado, cotação de parceiro ou promessa de melhor rota.
- Aprovar legalidade, KYC/AML, tributação ou qualquer decisão jurídica/regulatória.
- Autenticação, multiempresa, permissões, workflow corporativo de aprovação ou armazenamento de dado real de cliente.
- Gestão de carteira, hedge automatizado, previsão de caixa ou IA generativa.
- Rota stablecoin no MVP; o Depeg Risk Engine existente permanece como componente de pesquisa/portfólio até que haja requisito e fonte de dado apropriados.

## 4. Regras de negócio

### Cálculo

Para cada cotação:

```text
valor_principal_brl = valor_fatura_usd × taxa_usd_brl
custo_total_brl = valor_principal_brl + tarifa_brl
custo_percentual = tarifa_brl / valor_principal_brl
exposicao_liquida_usd_30d = recebimentos_usd_30d − pagamentos_usd_30d − valor_fatura_usd
```

O cálculo usa exclusivamente os valores declarados pelo usuário. Não aplica spreads, gas, PTAX ou premissas de mercado ocultas.

### Estados

- `INCOMPLETO`: fatura, duas cotações válidas ou timestamps não estão presentes.
- `REVISAR`: há dado vencido, prazo acima da política, custo acima da política, fatura acima da alçada ou exposição líquida negativa após a fatura.
- `PRONTO_PARA_APROVACAO`: todos os dados obrigatórios estão presentes e nenhuma regra interna foi violada. Não significa que a operação é legal nem que deve ser executada.

### Dados vencidos

Cotação com mais horas que a validade máxima declarada na política é exibida, mas força `REVISAR`. O limite é configurável por decisão e visível na tela.

## 5. Critérios de aceitação

1. Com uma fatura válida e duas cotações válidas, o sistema ordena alternativas por `custo_total_brl` e mostra a decomposição do cálculo.
2. O pacote expõe fonte declarada, horário, prazo, exposição líquida e cada alerta acionado.
3. Falta de dado obrigatório nunca produz recomendação: gera `INCOMPLETO` e lista o que falta.
4. Cotação vencida, limite de custo/prazo/alçada ou exposição líquida negativa produz `REVISAR`, com o mecanismo específico.
5. Não existe texto que classifique transação como permitida, ilegal, aprovada ou recomendada sem condição.
6. Com dados de exemplo, o pacote é produzido em até cinco minutos de preenchimento manual e permite que um revisor reproduza o resultado sem abrir planilha auxiliar.
7. Testes cobrem cálculo, estados, cada alerta e ausência de campos.

## 6. Riscos e restrições

| Risco | Mitigação no MVP |
|---|---|
| Usuário confundir sinal de política com parecer jurídico | Linguagem restrita a `REVISAR`/`PRONTO_PARA_APROVACAO`; disclaimer explícito. |
| Dados digitados incorretamente | Campos tipados, validação de domínio e exposição de premissas; não há enriquecimento oculto. |
| Produto não superar planilha | Saída deve condensar política, evidência temporal e explicação em um artefato único; teste com caso completo. |
| Uso de dado financeiro real | MVP usa apenas dados sintéticos; nenhuma persistência de cliente. |
| Scope creep para integração/execução | Fora de escopo explícito; qualquer nova dependência requer nova spec e ADR quando arquitetural. |

## 7. Input-policy-check

- **PII/credenciais/dado financeiro real:** proibidos nesta implementação; usar somente dados sintéticos.
- **Escopo:** limitado aos itens da seção 3.
- **Aprovação:** Luiz Maibashi revisa spec, diff e gates antes de qualquer commit/merge.

## 8. Evidências e gates planejados

1. Testes de unidade para cálculo, validade temporal e estados.
2. Teste de integração da tela com cenário sintético de fatura + duas cotações.
3. `pytest -q` sem chamadas de rede para testes novos.
4. Revisão do diff e quiz de aprendizado antes de commit.
5. PAVC pós-implementação para fronteiras de política, temporalidade e dados incompletos.

## 9. Saída esperada

Uma única página do dashboard demonstra o fluxo completo e deixa claro que a decisão ainda depende de aprovação humana e execução por parceiro autorizado.
