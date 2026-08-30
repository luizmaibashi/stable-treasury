# ADR-0014: Dashboard modular com Depeg Risk Engine como narrativa principal

**Data:** 2026-08-30
**Status:** Accepted
**Proposto por:** Luiz Maibashi

## Contexto

O dashboard concentra seis fluxos de interface em `app.py`, misturando bootstrap,
cache, widgets, I/O e narrativa. Após o gate documental encerrar a hipótese de
produto do dossiê pré-pagamento, o valor do projeto para portfólio passa a ser a
clareza da engenharia: o Depeg Risk Engine, seus dados históricos e suas limitações
devem abrir a demonstração.

## Decisão

Criar `src/views/` com um renderizador por aba e reduzir `app.py` ao bootstrap,
cache de `get_engine()` e composição de tabs. A ordem passa a ser: Risco de Depeg,
Liquidez, Trilhos, Compliance, Decisão pré-pagamento e Configuração.

## Consequências

**Positivas:**

- reduz o raio de mudança de cada fluxo de interface;
- torna a arquitetura navegável em revisão de portfólio;
- alinha a primeira experiência ao artefato quantitativo mais verificável.

**Negativas:**

- aumenta o número de arquivos e imports;
- não cria valor de mercado nem resolve débitos de dados/deploy;
- exige preservar cuidadosamente chaves do Streamlit durante a extração.

## Alternativas descartadas

| Alternativa | Motivo da rejeição |
|---|---|
| Manter `app.py` monolítico e só trocar a ordem das tabs | melhora a vitrine, mas mantém alto acoplamento e baixa legibilidade. |
| Migrar para Streamlit multipage | amplia navegação e configurações sem necessidade para a demonstração atual. |
| Reescrever domínio junto com a UI | mistura refatoração de apresentação com risco de regressão nos cálculos. |

## Validação

- `app.py` contém somente bootstrap/composição e o primeiro tab é o risco.
- `python -m pytest -q` passa integralmente.
- Inicialização visual local do Streamlit sem erro de importação.

## Referências

- `docs/spec/0002-refatoracao-dashboard-portfolio.md`
- `src/depeg_risk.py`
- `app.py`
