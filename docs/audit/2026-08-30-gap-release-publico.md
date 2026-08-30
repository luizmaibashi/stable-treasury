# Gap de release público — StableTreasury

**Data:** 2026-08-30  
**Status:** bloqueio de divulgação; nenhuma ação externa executada nesta análise.

## Fato observado

O estado local encerrou a tese comercial não validada e reposicionou o dashboard como
demonstração técnica do motor de risco. O commit local `78b7b1b` contém esse estado.

O repositório público continua com a narrativa anterior de "motor de decisão de tesouraria
cross-border" e de arbitragem em stablecoins. Portanto, ele não representa o artefato local
nem pode ser usado como evidência de um produto comercial validado.

Em 2026-08-29, a auditoria já havia identificado que GitHub e Streamlit estavam no commit
`c4f828f`, anterior às correções do ADR-0012. A diferença aumentou com o reposicionamento
e a refatoração de 2026-08-30.

## Risco e decisão

Divulgar o link atual mistura três coisas incompatíveis: uma interface antiga, dado histórico
sem compromisso de atualização e uma tese de produto que o gate de mercado encerrou.
O risco é reputacional: o portfólio passa a prometer mais do que o código e a evidência sustentam.

**Decisão:** não sincronizar, fazer push ou redeploy automaticamente. A operação externa exige
autorização explícita do proprietário e uma escolha de destino.

## Pré-condição de segurança

A senha da base Neon foi exposta em conversa anterior. Antes de qualquer publicação, o
proprietário deve rotacionar essa credencial no Neon e substituir a `DATABASE_URL` nos
Secrets do Streamlit. Não registrar a nova string em git, documentação, chat ou arquivo local
rastreado.

## Escolha pendente

### A. Manter como peça pública de portfólio

1. Rotacionar a credencial Neon e atualizar o Secret do Streamlit.
2. Decidir entre reingestão dos preços ou rótulo visível de demonstração histórica.
3. Com autorização explícita, sincronizar o subtree para o GitHub público e redeployar.
4. Conferir o dashboard publicado contra o commit liberado e remover toda promessa comercial
   não validada.

### B. Arquivar a peça pública

1. Rotacionar a credencial Neon de qualquer forma.
2. Com autorização explícita, substituir a descrição pública por um aviso de projeto arquivado
   ou suspender o app no Streamlit.
3. Manter apenas o código local e a trilha de auditoria como evidência de engenharia.

## Evidências relacionadas

- `docs/audit/2026-08-29-pavc-mvp-decisao-pre-pagamento.md`
- `docs/validation/0003-varredura-documental-mercado-e-concorrencia.md`
- `docs/spec/0002-refatoracao-dashboard-portfolio.md`
- [Repositório público atual](https://github.com/luizmaibashi/stable-treasury)
