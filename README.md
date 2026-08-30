# StableTreasury

[Abrir a demonstração pública](https://stable-treasury-khrmolkmu738evtrxd9aqv.streamlit.app/)

StableTreasury é uma demonstração de engenharia para investigar uma pergunta simples: o que acontece com a gestão de liquidez quando uma stablecoin perde a paridade com o dólar?

O centro do projeto é o Depeg Risk Engine. Ele lê o histórico de preço de USDC e USDT, calcula VaR e Expected Shortfall e mostra como o risco mudaria limites de exposição e o haircut de liquidez. A demonstração também traz cenários de custos por trilho, compliance e custo de carrego. São laboratórios determinísticos, não recomendações operacionais.

## O que vale observar

O gráfico histórico é o melhor ponto de partida. O evento do SVB, em março de 2023, aparece porque o preço do USDC caiu na série usada pelo cálculo. A data não foi programada no modelo.

Na aba Rail Comparator, o resultado é sempre um cenário. O sistema mostra as premissas, a sensibilidade ao spread de Wire e as limitações das fontes públicas. Se Binance ou PolygonScan não responderem, o cálculo continua com o fallback documentado e a tela identifica o modo degradado.

## Limites claros

Nada aqui executa pagamento, negocia câmbio, custodia ativo, gera cotação ou emite parecer jurídico. A hipótese de transformar esse trabalho em produto comercial foi pesquisada e encerrada: não foi encontrada evidência suficiente de uma lacuna frente a bancos, TMS e fluxos já existentes. O registro dessa decisão está em [Validação de mercado](docs/validation/0003-varredura-documental-mercado-e-concorrencia.md).

Os dados públicos têm latência, podem falhar e não são uma cotação em tempo real. O histórico persistido é atualizado sob demanda, com TTL de 24 horas, ingestão apenas do delta e fallback explícito para o último dado válido.

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

## Como o projeto se organiza

- `src/depeg_risk.py`: cálculo de VaR e Expected Shortfall.
- `src/ingestao.py`, `src/repositorio.py` e `src/db.py`: histórico e persistência.
- `src/comparador.py`: cenários de custo e estado de fallback das fontes monitoradas.
- `src/views/`: interface Streamlit.
- `tests/`: testes do comportamento determinístico.

A documentação foi separada por finalidade em [docs/](docs/README.md). Para entender o modelo, comece pelo [Deep Dive do Depeg Risk Engine](docs/DEEP_DIVE_DEPEG_ENGINE.md). Para dados e reprodução, veja a [proveniência](reports/proveniencia_stable_treasury.md).

Projeto de portfólio. Não é assessoria jurídica, fiscal ou de investimento.
