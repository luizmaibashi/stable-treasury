# Iteração 1 — intenção de negócio

## O Quê

**Intenção aprovada (provisória):** tornar o StableTreasury uma camada de decisão pré-pagamento para operações cross-border. Ele organiza a evidência de uma decisão, em vez de mover dinheiro.

## Por Quê

Importadores e tesourarias enfrentam custo, atraso, exposição e documentação; execução, câmbio e custódia já exigem parceiros regulados e têm incumbentes estabelecidos. O valor independente é reduzir a decisão mal fundamentada antes de selecionar esse parceiro.

## Como

### Fluxo alvo

1. Responsável registra fatura, moeda, vencimento, tipo de operação e fluxo previsto.
2. Anexa ou digita as cotações recebidas de parceiros autorizados e as condições de prazo.
3. Sistema calcula custo total comparável, exposição líquida, impacto de prazo no caixa e aderência a limites internos.
4. Sistema gera um **pacote de decisão**: dados usados e horário, premissas, alternativas, trade-offs, alertas e recomendação condicionada.
5. Um humano aprova e executa fora do produto, com o parceiro regulado escolhido.

### Escopo negativo obrigatório

- Não executa pagamento, câmbio, custódia ou transferência de ativo virtual.
- Não gera cotação bancária nem afirma ter o menor preço de mercado.
- Não aprova transação como legal/ilegal; apenas sinaliza política, informação ausente e necessidade de validação humana/jurídica.
- Não substitui TMS, ERP, corretora ou fornecedor de compliance.

### Métricas candidatas

- Custo efetivo cotado vs. opção aprovada, em R$ e % da fatura.
- Tempo entre recebimento da fatura e decisão aprovada.
- % de decisões com cotação, data/hora e premissas rastreáveis.
- % de operações fora da política detectadas antes da execução.

## Hipótese de comprador a aprofundar

Gerente financeiro de importador de porte médio, com pagamentos internacionais recorrentes e sem uma camada interna dedicada de tesouraria/TMS.

## Decisão pendente do gate D2

O usuário precisa explicar o fluxo em palavras próprias antes de a intenção ser considerada aprovada para spec.
