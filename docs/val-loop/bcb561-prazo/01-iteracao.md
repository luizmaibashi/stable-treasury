# Iteração 1 — A proximidade da BCB 561 (out/2026) invalida o projeto?

## O Quê
Validação da premissa: "a arbitragem stablecoin, base da narrativa do README, expira em ~3 meses — isso torna o projeto sem valor de portfolio?"

## Por Quê (risco)
Se verdadeiro, invalidaria a manchete central do README e exigiria reposicionamento urgente antes do deploy público.

## Como
Fluxo val-loop completo numa iteração (evidência interna + externa fortes o suficiente).

---
### Fase 0 — Contrato
- Critério de aprovação: o valor do projeto sobrevive à data de vigência da 561, ou depende inteiramente dela.
- Falsificabilidade: seria refutado se NENHUM componente do sistema tivesse valor fora da janela de arbitragem.
- Max iterações: 3 (usada 1).

### Fase 1 — Market Scan
| Ref | Fonte | Achado | Concorda/Contradiz |
|---|---|---|---|
| 1 | Grep interno (ADR-0002/0003/0008, README, Deep Dive) | Prazo já tratado como "diferencial de timing" desde o 1º pivot, não descoberta nova | Concorda com a tese do projeto |
| 2 | [Machado Meyer](https://www.machadomeyer.com.br/pt/inteligencia-juridica/publicacoes-ij/bancario-seguros-e-financeiro-ij/banco-central-altera-regras-do-efx) | Res. 561/26 publicada 30/abr/2026, vigência 1º/out/2026 confirmada | Confirma data usada no projeto |
| 3 | [Finsiders Brasil](https://finsidersbrasil.com.br/regulamentacao/resolucao-bcb-561-efx-stablecoins-pagamentos-internacionais/) | Restrição é **escopada a eFX** (nicho específico), não proibição geral de stablecoin | **Achado novo** — projeto já modela esse escopo corretamente (`tipo_operacao == "eletronico_cambio"`), mas não documentava a persistência fora do eFX |
| 4 | [MercGroup](https://www.mercgroup.com.br/insights/bcb-561-efx-investimentos-exterior-vigencia-outubro) | Prestadores não autorizados podem operar até mai/2027 solicitando licença | Nuance de transição, não muda a tese central |

### Fase 2 — Intent
Intenção de negócio real do projeto: NÃO é "vender uma arbitragem eterna". São 3 valores independentes:
1. Depeg Risk Engine (VaR/ES) — motor de risco quant, sem prazo de validade.
2. Compliance Filter — prova de engenharia *regulatory-aware*, que antecipa a regra.
3. Arbitragem — mensurada COM seu prazo, não escondido dele; e agora sabidamente mais restrita a eFX do que a "todo pagamento cross-border".

Gap encontrado: README não menciona a persistência fora do eFX — informação nova, não estava errada, estava incompleta.

### Fase 3 — Cenários
| Cenário | Esperado | Real | Status |
|---|---|---|---|
| Hoje (pré-out/2026) | Demo funciona plena | Confirmado | ✅ |
| Pós-out/2026, dentro de eFX | Compliance Filter bloqueia | Já implementado e testado (`test_filtrar_trilhos_eFX`) | ✅ |
| Pós-out/2026, fora de eFX | Arbitragem persiste | Confirmado pela Fase 1 (achado novo) | ✅ novo dado |
| Avaliador lê o projeto em 2027 | Vê regra corretamente antecipada | Compliance tab demonstra isso ao vivo | ✅ reforça, não enfraquece |

### Fase 4 — Crítica
- **DA1**: "Manchete do README fica desatualizada em 3 meses" → Mitigação: já enquadrada como *feature* (data de expiração conhecida), não bug oculto.
- **DA2**: "Leitor rápido pode achar que o projeto 'morre' em out/2026" → Mitigação real necessária: reforçar que (a) Depeg Engine não expira, (b) arbitragem persiste fora do eFX.
- **DA3**: "O projeto nunca executa transação real (escopo negativo ADR-0003), então nunca violaria a 561 de fato" → Isso é ponto a favor: ele MODELA a regra corretamente, não a viola nunca.
- Edge cases (5/5 testados na Fase 3, todos ✅).
- Gap de explicabilidade: nenhum — a lógica já estava certa no código; faltava só a frase no README.

### Fase 5 — Ajustes
| # | O que mudou | Por quê | Impacto |
|---|---|---|---|
| 1 | README ganha nota explícita: arbitragem persiste fora do escopo eFX + Depeg Engine não expira | Achado novo da Fase 1; fecha o gap do DA2 | Reforça a narrativa sem exigir mudança de código |

### Fase 6 — Veredito
- Critérios batidos: ✅ SIM — projeto NÃO é invalidado.
- Aprendizado da iteração: a Compliance Filter estava mais correta do que o README comunicava; o prazo é feature genuína, não fragilidade.
- Próximo passo: aplicar o ajuste de README (Fase 5 #1) e prosseguir com o push do repo público.
