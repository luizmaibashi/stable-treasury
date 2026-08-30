# Spec 0002 — Refatoração do dashboard para portfólio técnico

**Status:** implementada e verificada
**Data:** 2026-08-30
**Dono da aprovação:** Luiz Maibashi

## Objetivo

Reorganizar o dashboard Streamlit para tornar o Depeg Risk Engine a narrativa
principal do portfólio e reduzir o acoplamento de `app.py`, sem alterar cálculos,
regras de negócio, fontes de dados ou promessas do projeto.

**ROI de portfólio:** um revisor deve conseguir identificar em segundos a tese
técnica (risco de depeg baseado em histórico) e localizar cada fluxo de interface
sem navegar por um arquivo monolítico de aproximadamente 600 linhas.

## Escopo

### Incluído

1. Mover a renderização de cada aba para um módulo em `src/views/`.
2. Deixar `app.py` responsável apenas por bootstrap, cache de engine e composição
   das abas.
3. Reordenar a interface: risco de depeg primeiro; liquidez, trilhos e compliance
   como laboratórios consumidores; decisão pré-pagamento como demonstração
   determinística; configuração por último.
4. Ajustar textos de interface que ainda apresentem a demonstração pré-pagamento
   como produto validado.
5. Preservar os 107 testes existentes e a ausência de I/O de mercado no motor
   `decisao_pre_pagamento.py`.

### Fora de escopo

- Alterar fórmulas, limites, alertas, fontes de dados ou modelos de risco.
- Adicionar integração, execução financeira, IA, autenticação ou persistência nova.
- Converter o projeto para Streamlit multipage, trocar bibliotecas ou redesenhar a
  identidade visual.
- Corrigir débitos técnicos históricos não relacionados à fronteira de interface.

## Contrato de módulos

| Módulo | Responsabilidade | Dependência explícita |
|---|---|---|
| `src/views/risco_depeg.py` | gráfico histórico e leitura de snapshots | `engine` |
| `src/views/liquidez.py` | formulário e resultado do otimizador | nenhuma |
| `src/views/comparador.py` | comparador de trilhos | nenhuma |
| `src/views/compliance.py` | validador BCB demonstrativo | nenhuma |
| `src/views/decisao_pre_pagamento.py` | dossiê sintético fail-safe | nenhuma |
| `src/views/configuracao.py` | cotações e estado de sessão | nenhuma |
| `app.py` | configuração, cache e composição | `get_engine` |

## Critérios de aceitação

1. `app.py` não contém widgets de regra de negócio das abas nem imports de motores
   de domínio, exceto `get_engine`.
2. O primeiro tab visível é “Risco de Depeg”.
3. Cada aba mantém os controles e resultados já existentes; a única mudança
   intencional de texto é declarar a decisão pré-pagamento como demonstração.
4. `python -m pytest -q` passa integralmente.
5. O dashboard inicia sem erro de importação com `streamlit run app.py`.
6. Não há PII, credenciais ou dados financeiros reais no diff.

## Input-policy-check

- **Dados sensíveis:** não usar; a demonstração continua sintética.
- **Escopo autorizado:** somente refatoração de interface e narrativa de portfólio.
- **Aprovação de merge:** Luiz revisa o diff e decide sobre commit; push é proibido
  sem autorização explícita.

## Riscos

- Mover widgets pode alterar chaves de `session_state` ou estado entre reruns.
  Mitigação: preservar nomes de chave e rodar a suíte completa.
- Imports circulares entre views e domínio podem quebrar o startup. Mitigação:
  dependências de domínio ficam no módulo que as consome; `app.py` não importa
  renderizadores de volta para domínio.
- A refatoração pode involuntariamente alterar a narrativa. Mitigação: manter os
  textos de limites e fazer revisão visual local após os testes.

## Evidência de implementação

- `app.py` foi reduzido a bootstrap, cache e composição de abas.
- Os seis renderizadores estão em `src/views/`.
- `python -m pytest -q`: 107 passed em 101,30 s (2026-08-30).
- QA local: as seis abas renderizaram; risco abre primeiro; console sem erros.
  A verificação capturou uma referência residual a `_engine` na view de risco,
  corrigida para a dependência explícita `engine` antes do gate final.
