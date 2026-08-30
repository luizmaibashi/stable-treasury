# PAVC — Refatoração do dashboard para portfólio

**Data:** 2026-08-30
**Escopo:** `app.py` e `src/views/`

## Advogado do Diabo

| Falha potencial | Mecanismo | Mitigação/evidência |
|---|---|---|
| Reordenar tabs altera estado entre reruns | Chaves de widgets podem mudar ou colidir | Os corpos e chaves foram extraídos sem renomear; cada fluxo permanece em seu módulo. |
| A view de risco quebra ao perder dependência implícita | A extração deixou uma chamada residual a `_engine()` | O QA visual capturou o erro antes do commit; a view agora recebe e usa `engine` explicitamente. |
| A refatoração muda cálculos silenciosamente | Código de domínio é movido junto com a UI | Nenhum arquivo em `src/` de domínio foi alterado; a suíte completa passou. |

## Explicabilidade

`app.py` configura Streamlit, disponibiliza um único engine cacheado e compõe as
abas. Cada arquivo em `src/views/` renderiza somente seu fluxo e importa os
motores de domínio que consome. O risco de depeg é exibido primeiro porque é o
artefato quantitativo mais verificável; a decisão pré-pagamento permanece como
demonstração sintética de falha segura, não como promessa comercial.

## Cenários de borda

| Cenário | Resultado | Evidência |
|---|---|---|
| Banco/snapshots indisponíveis | A aba de risco mostra aviso, sem derrubar a aplicação | tratamento preservado em `src/views/risco_depeg.py` |
| Nenhum estado de sessão anterior | Views usam os mesmos defaults e `get` já existentes | extração mecânica, sem novas chaves |
| Import de todas as views | Sem erro de sintaxe/importação | `py_compile` aprovado |
| Suíte de domínio completa | Sem regressão dos cálculos | 107 passed em 101,30 s |
| Seis abas e hero | Ordem, narrativa e renderização coerentes | QA visual local; console sem erros |

## Veredito

**Aprovado.** A fronteira entre orquestração e interface ficou explícita sem
alterar domínio, fontes ou escopo. A validação não prova comportamento comercial;
ela prova que a refatoração preservou a base técnica demonstrável.
