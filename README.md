# StableTreasury

[Abrir a demonstração pública](https://stable-treasury-khrmolkmu738evtrxd9aqv.streamlit.app/)

Uma stablecoin costuma entrar na conversa de tesouraria como se fosse apenas dólar em formato digital. Essa simplificação é confortável enquanto o preço está perto de US$ 1. Ela deixa de funcionar justamente no momento em que uma área de risco precisa de uma resposta: quando a paridade se rompe, quanto da liquidez ainda pode ser tratada como disponível?

O StableTreasury nasceu para tornar essa pergunta visível e verificável. É uma demonstração pública de engenharia de risco e dados para tesouraria. O projeto reconstrói o comportamento de USDC e USDT a partir de histórico público, mede o tamanho das perdas na cauda e traduz o resultado em limites de exposição e haircut de liquidez.

## A pergunta que este projeto responde

Uma empresa que usa stablecoin como capital de giro em um fluxo internacional precisa separar duas coisas que parecem iguais em períodos calmos: o saldo exibido na carteira e a liquidez que continua disponível sob estresse.

O Depeg Risk Engine calcula VaR e Expected Shortfall sobre o histórico de peg. Em vez de assumir que USDC e USDT valem sempre US$ 1, ele pergunta o que teria acontecido nos piores pontos observados da série. O evento do Silicon Valley Bank, em março de 2023, aparece naturalmente no gráfico porque o USDC de fato caiu naquele período. Não há um marcador colocado para contar uma história depois do resultado.

Na prática, a demonstração mostra como uma regra de tesouraria poderia reagir: reduzir o teto de exposição, aplicar um haircut ao valor líquido da posição e deixar explícita a premissa usada. Isso não substitui política, cotação ou aprovação humana. É o motor de cálculo e a trilha de evidências que uma decisão séria exigiria antes desses passos.

## Por que isso interessa a quem trabalha com tesouraria e risco

O problema não é descobrir que há risco em stablecoin. Isso já é conhecido. A dificuldade é sair de frases genéricas como “o ativo é seguro” ou “o risco é baixo” e chegar a uma regra que possa ser revisada quando o mercado muda.

Aqui, a discussão vira algo auditável:

- qual histórico foi usado;
- qual nível de confiança e janela entram no cálculo;
- qual perda de cauda reduz a liquidez reconhecida;
- em que ponto uma fonte pública falhou e qual fallback assumiu seu lugar.

Para uma pessoa de tesouraria, o ganho é enxergar a diferença entre disponibilidade nominal e disponibilidade ajustada a risco. Para risco, compliance e auditoria, é conseguir rastrear premissas e limites. Para engenharia de dados, o projeto mostra como transformar uma série pública imperfeita em um cálculo reprodutível, com persistência, atualização controlada e falha explícita.

## O que você encontra na demonstração

### Depeg Risk Engine

É o núcleo do projeto. A aba usa o histórico de USDC e USDT para calcular VaR, Expected Shortfall e um haircut de liquidez. Também exibe snapshots históricos para que seja possível comparar o risco atual com eventos anteriores, em vez de olhar apenas o número do dia.

### Rail Comparator

Um laboratório de cenários para comparar o custo total de trilhos de pagamento. Ele separa spread, IOF, tarifa, on-ramp, off-ramp e gas. A intenção é deixar claro qual premissa move o resultado, especialmente o spread negociado de Wire. O resultado é uma simulação, não uma cotação e nem uma instrução de pagamento.

### Compliance e custo de carrego

As outras abas mostram como regras regulatórias e o custo de oportunidade do caixa mudam a leitura de uma posição. São cenários determinísticos, com limites de uso documentados, para evitar que um dashboard pareça mais preciso do que as suas fontes permitem.

## Como ler o projeto em cinco minutos

1. Abra o [Depeg Risk Engine](https://stable-treasury-khrmolkmu738evtrxd9aqv.streamlit.app/) e observe o gráfico histórico. Procure o período de março de 2023 e compare o comportamento do USDC com o do USDT.
2. Veja o VaR, o Expected Shortfall e o haircut. Eles respondem a perguntas diferentes: perda em um limiar, perda média nos piores casos e impacto na liquidez reconhecida.
3. Passe pelo Rail Comparator e altere o spread de Wire. A fronteira de indiferença mostra em qual ponto a conclusão entre Wire e stablecoin muda.
4. Se aparecer o aviso de modo degradado, leia-o. Ele informa que Binance ou PolygonScan ficaram indisponíveis, qual cálculo recebeu fallback e qual premissa entrou no lugar. O sistema continua funcionando, mas não disfarça a perda de qualidade do dado.

## Engenharia por trás da tela

O dashboard não depende de uma atualização opaca em segundo plano. Ao abrir a aplicação, o histórico é atualizado sob demanda somente se estiver vencido há mais de 24 horas. A ingestão busca apenas o delta, reaproveita um dia de sobreposição para evitar lacunas e usa advisory lock no Postgres para impedir duas atualizações concorrentes.

Se a fonte não responder, o contrato é falhar de forma compreensível: o histórico persistido mais recente é mantido e a interface identifica o estado degradado quando o fallback do Rail Comparator é usado. Isso é importante porque dado indisponível não deveria virar um número aparentemente preciso sem deixar rastros.

O projeto usa Streamlit, Python, SQLAlchemy e Postgres. Em produção, o banco é Neon; no desenvolvimento, há Postgres via Docker. A intenção é manter o mesmo modelo de persistência nos dois ambientes e reduzir surpresas de dialeto ou conexão.

## O que este projeto não faz

Ele não executa pagamentos, não custodia ativos, não negocia câmbio, não gera cotações e não emite parecer jurídico, fiscal ou de investimento. O caso comercial de pré-pagamento foi investigado e encerrado porque não houve evidência suficiente de uma lacuna frente a bancos, TMS e fluxos já existentes. A [validação de mercado](docs/validation/0003-varredura-documental-mercado-e-concorrencia.md) registra essa decisão.

O StableTreasury permanece como portfólio porque o problema técnico continua útil: medir risco de depeg com dados reais, tornar premissas revisáveis e expor o que acontece quando a fonte de dados falha.

## Rodar localmente

```bash
pip install -r requirements.txt
docker compose up -d
python -m scripts.seed_db
streamlit run app.py
```

Para executar os testes:

```bash
python -m pytest -q
```

## Estrutura do repositório

- `src/depeg_risk.py`: cálculo de VaR, Expected Shortfall e faixas de risco.
- `src/ingestao.py`, `src/repositorio.py` e `src/db.py`: ingestão, histórico e persistência.
- `src/comparador.py`: cenários de custo e estado de fallback das fontes monitoradas.
- `src/views/`: interface Streamlit.
- `tests/`: comportamento determinístico e cenários de falha.

Para aprofundar, comece pelo [Deep Dive do Depeg Risk Engine](docs/DEEP_DIVE_DEPEG_ENGINE.md). A [proveniência dos dados](reports/proveniencia_stable_treasury.md) explica fonte, atualização e como reproduzir a ingestão. O [índice da documentação](docs/README.md) reúne o restante.

Projeto de portfólio, construído para discussão técnica e avaliação de engenharia.
