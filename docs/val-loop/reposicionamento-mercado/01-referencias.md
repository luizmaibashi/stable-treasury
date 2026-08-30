# Iteração 1 — referências de mercado

## O Quê

Varredura de dor, concorrência e restrição regulatória para testar o reposicionamento do StableTreasury.

## Por Quê

Evitar transformar uma demo de stablecoin em produto de pagamento que compete com infraestrutura regulada e incumbentes.

## Como

Leitura de fontes primárias, associações de tesouraria e pesquisa setorial. Fontes comerciais foram tratadas como evidência atribuída, não como fato independente.

| Ref. | Fonte | Achado | Leitura para a hipótese |
|---|---|---|---|
| Dor de importador | [Nextrade, 2026](https://www.nextradegroupllc.com/crossborder-payments) | Pesquisa com 2.100 pequenos importadores em sete mercados, incluindo Brasil: 72% reportam taxas altas, 65% demora, 62% controles de FX; 61% têm custo operacional oculto de US$100+ por operação. | **Confirma** dor de custo, prazo e documentação em importadores pequenos. Limite: amostra internacional/e-commerce, não prova compra de software no Brasil. |
| Tesouraria corporativa | [PwC Global Treasury Survey 2025](https://www.pwc.com/us/en/services/consulting/finance-accounting-transformation/library/2025-global-treasury-survey.html) | 36% dos respondentes ainda têm processo manual de exposição cambial; FX foi a exposição econômica crítica para 83%. Em forecasting, 38% das empresas >US$10 bi e 52% das de US$1–10 bi consolidam dados manualmente. | **Confirma** dor de visibilidade/decisão. **Refuta** entrar direto em enterprise: 94% já operam TMS e há alto custo de integração. |
| Multinacionais | [EACT Treasury Survey 2025](https://eact.eu/articles/results-of-2025-eact-survey/) | Visibilidade de caixa, risco de mercado e infraestrutura TMS são prioridades; há processos manuais em FX e foco em controles. IA/DLT ficam abaixo de necessidades básicas de dados e padronização. | **Refuta** vender “IA/stablecoin” como protagonista. **Confirma** ferramenta que gere controle e explicação de decisão. |
| Regulação | [Resolução BCB 561](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=561&tipo=Resolu%C3%A7%C3%A3o+BCB) e [nota do BCB](https://www.bcb.gov.br/detalhenoticia/21110/nota) | eFX passa a ser restrito a instituições autorizadas; a norma muda o contexto de liquidação internacional. | **Refuta** promessa de executar rota com stablecoin sem parceiro regulado. **Confirma** produto de decisão, evidência e controle — jamais parecer jurídico. |
| Concorrência vertical | [Codexa/Circle, 2026](https://www.circle.com/case-studies/codexa) | Plataforma brasileira já combina desembaraço, câmbio e pagamentos; opera corretora de câmbio regulada e abstrai a infraestrutura de USDC para importadores/exportadores. | **Refuta** competir como orquestrador ou executor de pagamento. O valor precisa estar antes da execução: diagnóstico, política, simulação ou evidência de decisão. Fonte comercial; números são auto-relatados. |
| Concorrência institucional | [Ripple no Brasil, 2026](https://ripple.com/ripple-press/ripple-deepens-commitment-to-brazil-with-expanded-payments-offering-growing-customer-momentum-and-vosp-license-application/) | Incumbente anuncia stack institucional de pagamentos, custódia e tesouraria e busca licença VASP. | **Refuta** infraestrutura como wedge para primeira versão. Fonte comercial, usada apenas para mapear capacidade competitiva. |
| Dados abertos | [Comex Stat / MDIC](https://www.gov.br/pt-br/servicos/consultar-estatisticas-oficiais-do-comercio-exterior-de-bens-brasileiro) | Dados gratuitos, detalhados e mensais de importação/exportação desde 1997. | **Confirma** fonte pública para segmentar corredores/setores e construir benchmark; não traz preços bancários nem exposição financeira por empresa. |

## Síntese provisória

Há dor mensurável em pagamentos e tesouraria cross-border, mas a execução financeira é mercado regulado e já ocupado. O wedge plausível não é “pagar por stablecoin”: é dar ao responsável financeiro uma decisão explicável de **custo total, prazo, exposição e política** antes de selecionar um parceiro regulado.

## Lacunas que a internet não fecha

1. Qual segmento brasileiro tem dor suficiente e acesso comercial para pagar.
2. Quais dados de cotação e prazo podem ser obtidos sem parceria bancária.
3. Se o comprador usaria o artefato em fluxo real ou apenas como material de comitê.
