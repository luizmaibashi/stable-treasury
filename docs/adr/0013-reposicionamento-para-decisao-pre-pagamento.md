# ADR-0013: Reposicionar para decisão pré-pagamento

**Data:** 2026-08-29  
**Status:** Accepted  
**Proposto por:** Luiz Maibashi  
**Contexto:** StableTreasury

## 1. Contexto

O StableTreasury nasceu como motor de comparação de trilhos, risco de depeg e alocação de liquidez. A validação de mercado de 2026-08-29 encontrou dor real em custo, prazo, FX e documentação de pagamentos cross-border, mas também duas restrições: execução financeira exige parceiros regulados e o mercado já possui incumbentes de infraestrutura.

**Termos:** decisão pré-pagamento, pacote de decisão, cotação anexada, parceiro regulado.

**Restrições:**
- Não executar pagamentos, câmbio, custódia ou transferências.
- Não emitir parecer jurídico ou aprovação regulatória.
- Não prometer cotação de mercado sem fonte bancária/parceira verificável.

## 2. Decisão

O StableTreasury passa a priorizar um pacote auditável de decisão pré-pagamento: recebe fatura, fluxo, cotações e política; calcula custo total, prazo, impacto de caixa, exposição e alertas; e registra a recomendação condicionada. A aprovação e a execução permanecem humanas e externas ao produto.

**Razão principal (ROI):** se não fizermos, o projeto continua uma demo de comparador sem comprador definido e concorre com infraestrutura regulada. Se fizermos, pode reduzir retrabalho e tornar rastreável uma decisão que hoje depende de planilhas, e-mails e cotações dispersas.

## 3. Consequências

**Positivas:**
- Dor de negócio é independente de stablecoin e sobrevive a mudanças regulatórias.
- Reduz fronteira regulatória e técnica do MVP.
- Preserva os módulos atuais de risco, custo e política como insumos explicáveis.

**Negativas:**
- Não há ainda evidência de disposição de compra.
- Precisa provar que o pacote é superior a uma planilha estruturada.
- Cotações continuarão sendo fornecidas pelo usuário até haver parceria/integracão autorizada.

## 4. Alternativas descartadas

| Opção | Vantagem | Por que foi rejeitada |
|---|---|---|
| Executar pagamentos com stablecoin | Demonstra economia e rapidez | Exige licença/parceiro, entra em mercado concorrido e é sensível a regulação. |
| Virar TMS completo | Ataca todo ciclo de tesouraria | Integração e venda enterprise inviáveis para o MVP. |
| Manter demo de portfólio | Custo zero | Não cria uma hipótese de valor testável no mercado. |

## 5. Impacto e validação

**Métricas de sucesso da spec futura:** `custo_total_brl`, `prazo_settlement`, `exposicao_liquida_usd_30d`, `timestamp_cotacao`, `status_politica` e `pacote_decisao` devem tornar a decisão reproduzível.

**Critério de validação:** um caso com fatura e duas cotações precisa produzir recomendação com premissas explícitas e informação faltante bloqueante. Se não superar uma planilha bem feita, esta direção é descartada.

## 6. Referências

- Registro interno de validação de mercado, arquivado fora da árvore pública
- `docs/adr/0012-auditoria-2026-07-30-correcoes.md`
- [Pesquisa Nextrade](https://www.nextradegroupllc.com/crossborder-payments)
- [PwC Global Treasury Survey 2025](https://www.pwc.com/us/en/services/consulting/finance-accounting-transformation/library/2025-global-treasury-survey.html)
