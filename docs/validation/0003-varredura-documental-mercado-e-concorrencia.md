# Varredura documental 0003 — Mercado e concorrência

**Data da pesquisa:** 2026-08-30
**Status:** evidência secundária; não valida adoção nem disposição a pagar
**Objeto:** o pacote de decisão pré-pagamento para importador B2B industrial

## Veredito executivo

Há evidência pública de que tesourarias lidam com processos manuais, melhoria de
pagamentos, planilhas e comparação de cotações. Também há operação cambial de
importação relevante e observável no Brasil. Isto torna a **dor estrutural
plausível**, mas não prova que o StableTreasury, como produto autônomo, resolve
uma lacuna vendável.

O mercado é mais ocupado do que a hipótese inicial assume: portais bancários e
TMS já cobrem execução, cotação, acompanhamento, política e/ou auditoria. A
única brecha ainda possível é estreita: uma camada independente para comparar
cotações já recebidas de múltiplos parceiros e produzir evidência de revisão sem
executar pagamento, exigir ERP ou substituir TMS. Nenhuma fonte encontrada prova
que importadores médios brasileiros demandam essa camada.

**Decisão atual: NÃO ampliar o MVP.** A tese só continua como investigação se a
próxima varredura demonstrar essa brecha de forma verificável; não é permitido
alegar validação de mercado a partir deste documento.

## Evidência da dor e do contexto

| Achado | Fonte e força | Leitura correta |
|---|---|---|
| Em benchmarking de 2025, automação de processos manuais (57%) e melhoria de processos de pagamentos (51%) aparecem entre os desafios mais citados; empresas menores (< US$ 1 bi de receita) tendem a ter 1–3 FTEs de tesouraria. | [AFP, 2025](https://www.afponline.org/training-resources/resources/articles/Details/examining-benchmarks-for-treasury-teams/) — associação profissional; pesquisa citada, não específica do Brasil/ICP. | Sustenta que a operação é enxuta e manual, não que este dossiê é a solução. |
| A AFP descreve planilhas como ferramenta essencial, mas frágil em controle de versões, colaboração e erros de fórmula; múltiplos portais bancários aumentam a complexidade. | [AFP, tecnologia em tesouraria](https://www.afponline.org/topics/treasury/technology-in-treasury) — associação profissional; qualitativa. | Sustenta a hipótese de evidência dispersa e rastreabilidade, sem quantificar o problema no Brasil. |
| Profissionais relataram desde fluxo automatizado até ligar manualmente para bancos, obter taxas e comparar propostas. | [AFP, práticas de FX](https://www.afponline.org/training-resources/resources/articles/Details/treasury-professionals-discuss-getting-the-best-rates-on-fx) — relato APAC de 2022. | Sustenta o mecanismo de “duas cotações”, mas é antigo e fora do segmento brasileiro. |
| O BCB publica mensalmente quantidade e valor de operações de câmbio, incluindo importação; o MDIC mantém dados oficiais detalhados de importação atualizados mensalmente. | [BCB, ranking de câmbio](https://www.bcb.gov.br/estatisticas/rankingcambioinstituicoes?ano=2025), [MDIC/Comex Stat](https://www.gov.br/pt-br/servicos/consultar-estatisticas-oficiais-do-comercio-exterior-de-bens-brasileiro) — fontes primárias. | Confirma que o domínio transacional existe; não segmenta importador industrial médio nem seu processo de aprovação. |
| Painel qualitativo de PMEs no Brasil, México e Colômbia: 9 em 10 considerariam trocar de provedor cross-border; os motivos citados incluem previsibilidade de liquidação, transparência de tarifas/valor final, menos processos manuais e menos exceções. | [Mastercard + FXC Intelligence, 2026](https://www.mastercard.com/news/latin-america/pt-br/noticias/comunicados-de-imprensa/pr-pt/2026/junho/pagamentos-cross-border-se-tornam-um-campo-de-disputa-pela-lealdade-na-america-latina-e-no-caribe-aponta-pesquisa-da-mastercard-e-da-fxc-intelligence/) — pesquisa qualitativa divulgada por fornecedor; sem tamanho da amostra na página. | Evidência regional da dor, mas o comportamento observado é trocar **provedor de pagamento**, não adotar uma ferramenta independente de pré-decisão. |
| Uma corretora brasileira oferece uma planilha gratuita para gestão cambial, prometendo cenários, planejamento de pagamentos/recebimentos e visibilidade de despesas/spread. | [Broker Brasil](https://materiais.brokerbrasilcambio.com.br/planilha-de-gestao-de-cambio) — marketing de fornecedor. | O baseline de planilha não é hipotético nem fraco; é uma alternativa de custo marginal próximo de zero. |
| Uma fintech de agregação de dados descreve planilhas paralelas e múltiplos bancos consultados por telefone em remessas internacionais. | [Datanomik](https://www.datanomik.com/entre-tesoureiros/pagamentos-internacionais-como-estruturar-uma-operacao-eficiente-de-ponta-a-ponta-na-tesouraria) — marketing de fornecedor; sem método público. | É uma pista para busca, não prova independente. O próprio fornecedor vende integração/controle, portanto também é alternativa adjacente. |
| Discussão recente sobre TMS afirma que empresas médias ainda percebem TMS como caro e pesado em TI; o entrevistado reconhece que custo continua sendo obstáculo, apesar do SaaS reduzir manutenção e implantação. | [Treasury Management International / Cobase, 2025](https://treasury-management.com/articles/access-to-power) — entrevista com fornecedor de TMS; não é pesquisa independente nem recorte brasileiro. | Sustenta uma possível barreira de adoção, mas também mostra que TMS SaaS disputa exatamente essa barreira. Não assumir que ela cria espaço para o StableTreasury. |
| Plataforma brasileira para **correspondentes cambiais** declara operar com múltiplos bancos, cotações, contratos e acompanhamento de DUIMP/SWIFT. | [Tech Câmbio](https://www.techcambio.com.br/) — marketing de fornecedor, público-alvo não é o importador. | A consolidação multibanco já existe do lado do intermediário. Isso enfraquece a hipótese de que o importador necessariamente precisa fazê-la em uma ferramenta própria. |

## Mapa competitivo público

`Sim` significa que a fonte pública declara explicitamente a capacidade. `—`
significa que a fonte consultada não a comprova; não significa ausência do
produto. Declarações de fornecedor são material de marketing, não evidência de
resultado para cliente.

| Oferta | Cotar/fechar câmbio | Execução ou acompanhamento | Política/aprovação/auditoria | Comparar cotações de múltiplos parceiros | Dependência de integração | Consequência para a tese |
|---|---|---|---|---|---|---|
| [Banco do Brasil — Central de Câmbio](https://www.bb.com.br/site/moeda-estrangeira/cambio-online/) | Sim, da cotação à contratação | Sim | Acompanhamento e monitoramento declarados | — | Não documentada na página | Resolve o fluxo dentro de um único banco; não prova comparação independente. |
| [Santander — Negócios Internacionais](https://www.santander.com.br/comercio-exterior-e-cambio/portal-de-negocios-internacionais/) | Sim, cotação em tempo real e contratação | Sim | Rastreamento e documentação; integração ERP por API opcional | — | API disponível, mas uso sem API também é declarado | Confirma que importação e câmbio já têm canal digital especializado. |
| [Bradesco Net Empresa](https://banco.bradesco/cambionoapp/) | Sim, câmbio pronto | Sim, acompanha até liquidação | Pendências e histórico de cotações | — | Não documentada na página | Reforça que cotar e acompanhar uma operação não é diferenciação. |
| [FXPort / Comexport](https://fxport.com.br/) | Sim, a fonte declara “melhores taxas” | Sim, processo fim a fim | Gestão e controle declarados | — | Não documentada na página | Concorrente adjacente para importação/exportação; profundidade de comparação não é verificável na fonte pública. |
| [XEND Exchange](https://www.xend.exchange/) | Cotações firmes de parceiros antes do fechamento | Sim, conecta a parceiros regulados | Documentação e aprovação manual são descritas | Não comprovado | Não documentada na página | É o adjacente mais próximo: narra a mesma fricção, mas vende execução. |
| [FIS Treasury](https://www.fisglobal.com/-/media/fisglobal/files/pdf/brochure/treasury-and-risk-solutions-overview.pdf) | Sim | Sim | Workflow de autorização, segregação de funções e aprovações em camadas | Sim, “quote management for competitive analysis” | Conectividade a plataformas declarada | Prova que a capacidade existe em TMS enterprise; torna falsa qualquer alegação de novidade funcional. |
| [Kyriba Payments](https://www.kyriba.com/products/payments/) | Não é o foco da página | Sim, payment hub | Política, aprovações em múltiplos níveis e trilha de auditoria | — | Conectividade ERP-banco é central na proposta | Reforça a fronteira: TMS/hub resolve governança integrada, mas a implantação é outra categoria de custo/escopo. |
| [Broker Brasil — planilha de gestão cambial](https://materiais.brokerbrasilcambio.com.br/planilha-de-gestao-de-cambio) | Não fecha câmbio na página | — | Planejamento e visibilidade de despesas/spread declarados | — | Não | É o benchmark de custo zero mais próximo; o dossiê precisa superar essa planilha em rastreabilidade de exceções, não apenas calcular. |
| [Tech Câmbio](https://www.techcambio.com.br/) | Sim, via bancos parceiros | Sim | Operações, contratos e acompanhamento declarados | Sim, na camada do correspondente | Webhooks disponíveis | Não é concorrente direto de software para importador, mas dá ao correspondente uma alternativa para centralizar a complexidade e vender atendimento. |

## O que a pesquisa refuta e o que não refuta

| Hipótese | Estado | Evidência |
|---|---|---|
| “Importadores precisam de câmbio e pagamento internacional.” | Sustentada no nível macro | Estatísticas BCB/MDIC e ofertas bancárias específicas para importação. |
| “Equipes enxutas sofrem com processos manuais, planilhas e pagamento.” | Sustentada indiretamente | AFP; sem recorte Brasil/industrial médio. |
| “O StableTreasury é funcionalmente único.” | **Refutada** | FIS documenta gestão competitiva de cotações e workflow; bancos/TMS cobrem partes relevantes. |
| “Há uma lacuna leve, multibanco e sem execução para o ICP brasileiro.” | **Não comprovada** | Nenhuma fonte pública encontrada mede essa necessidade ou ausência de alternativa. |
| “O dossiê supera uma planilha em clareza para o decisor.” | **Não mensurável por desk research** | Exige observação de uso; não afirmar o contrário. |
| “A dor atual leva o ICP a comprar ferramenta de decisão independente.” | **Não comprovada e enfraquecida** | A pesquisa regional aponta para migração de provedor; planilhas gratuitas e portais são alternativas diretas. |
| “O custo/implantação de TMS deixa uma brecha para solução leve.” | Plausível, mas insuficiente | Fonte setorial de fornecedor relata a barreira; SaaS TMS também a ataca e não há prova de que o ICP brasileiro escolha uma camada separada. |

## Kill gate documental

Esta pesquisa só libera uma segunda rodada de desk research se forem encontradas
fontes independentes que satisfaçam **todos** os critérios abaixo:

1. uma fonte brasileira ou com recorte comparável que documente a fricção de
   consolidar múltiplas propostas/cotações para pagamento internacional;
2. uma fonte que mostre que o segmento-alvo não adota TMS/portal integrado para
   resolver a revisão — por custo, implantação ou processo;
3. nenhuma alternativa pública para o mesmo ICP que reúna, sem execução e sem
   integração obrigatória, comparação multibanco, política, caixa/exposição e
   trilha de revisão.

Se a rodada não encontrar os itens 1 e 2, ou encontrar uma oferta comparável que
cubra os três itens do ponto 3, encerrar o posicionamento de produto. O código
permanece apenas como demonstração de engenharia e raciocínio fail-safe, sem
alegação comercial.

## Veredito da busca limitada

**Gate documental: FALHOU — recomendação de encerrar o posicionamento como
produto.**

A busca limitada foi concluída sem satisfazer os critérios 1 e 2:

1. há relatos regionais de fricção em pagamentos cross-border, mas nenhuma fonte
   independente prova que o importador industrial médio brasileiro precisa
   consolidar **múltiplas cotações** em uma camada separada;
2. há evidência setorial de percepção de custo/complexidade de TMS, mas não uma
   medição independente no ICP brasileiro que demonstre bloqueio de adoção;
3. portais bancários, correspondentes multibanco, planilhas gratuitas e TMS
   cobrem ou aproximam partes relevantes do fluxo.

Logo, continuar construindo para “descobrir” a lacuna violaria o kill gate. O
MVP deve ser mantido como demonstração de engenharia determinística e fail-safe;
nenhuma feature, integração, IA ou alegação de product-market fit deve ser
adicionada sob este posicionamento.
