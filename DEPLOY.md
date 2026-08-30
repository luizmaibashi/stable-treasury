# Publicação do StableTreasury

O projeto público roda no Streamlit Community Cloud e usa Neon como banco Postgres. A versão atual está publicada como demonstração técnica em [stable-treasury.streamlit.app](https://stable-treasury-khrmolkmu738evtrxd9aqv.streamlit.app/).

## Pré-requisitos

- `DATABASE_URL` configurada nos Secrets do Streamlit, com `sslmode=require`.
- Banco semeado ao menos uma vez com `python -m scripts.seed_db`.
- Testes locais concluídos antes de publicar.

O segredo fica somente no ambiente local ou nos Secrets do Streamlit. Nunca em `.env`, `secrets.toml` ou commit.

## Atualizar o repositório público

O projeto vive dentro da base privada. Gere a árvore pública a partir do subdiretório e envie apenas esse snapshot:

```bash
git subtree split --prefix=PROJETOS/02_PORTFOLIO/stable-treasury <commit-base>
git push --force-with-lease https://github.com/luizmaibashi/stable-treasury.git <commit-subtree>:main
```

O uso de `--force-with-lease` é intencional: o histórico público é produzido pelo `subtree split`, não pelo histórico completo da base. Antes do push, confirme o hash remoto de `main`.

## Conferência após o deploy

1. Aguarde o redeploy automático do Streamlit.
2. Abra a demonstração e confira o gráfico de risco, o watermark do último histórico persistido e uma simulação do Rail Comparator.
3. Se a mudança introduziu um novo import em `app.py` ou em módulo carregado por ele, faça reboot do app no Streamlit. O hot reload pode manter módulos antigos em memória.
4. Quando uma fonte monitorada falhar, confira se o Rail Comparator mostra o modo degradado e a premissa de fallback.

O primeiro acesso depois de uma pausa do Neon pode ser mais lento. Isso é esperado no plano gratuito.
