# Deploy — StableTreasury (Streamlit Community Cloud + Neon)

> Guia passo a passo para colocar o app no ar com um **link público**, custo zero.
> O código **não muda** entre local e produção — só a variável `DATABASE_URL` (ADR-0005/0006).
> Tempo estimado: ~20 min. Nada aqui foi executado ainda — este é o checklist.

## Visão geral

```
  Repo público (GitHub)  ─────►  Streamlit Community Cloud  ─────►  link público
         │                              │
         │                              └── lê DATABASE_URL dos Secrets
         ▼
  Postgres na nuvem (Neon)  ◄──── você semeia uma vez (seed_db)
```

Três contas gratuitas: **GitHub** (código), **Neon** (banco), **Streamlit Cloud** (app).

---

## Passo 1 — Repo público próprio (extrair do monorepo, com histórico)

O projeto vive dentro de um monorepo privado. Vamos extraí-lo para um repo próprio e público,
**preservando os commits** (a trilha de ADRs/auditoria é parte do valor de portfolio).

1. Crie um repo **vazio e público** no GitHub (ex: `stable-treasury`). Não adicione README/licença
   (o push traz tudo).

2. Na raiz do monorepo, gere um branch só com o histórico deste subdiretório:
   ```bash
   cd /caminho/para/Base_de_Conhecimento
   git subtree split --prefix=PROJETOS/02_PORTFOLIO/stable-treasury -b stable-treasury-deploy
   ```
   Isso cria o branch `stable-treasury-deploy` com os arquivos do projeto **na raiz** (que é o
   que o Streamlit Cloud espera: `app.py` e `requirements.txt` no topo).

3. Faça push desse branch como `main` do repo novo:
   ```bash
   git push https://github.com/<seu-usuario>/stable-treasury.git stable-treasury-deploy:main
   ```

4. (Opcional) Confira no GitHub: `app.py`, `requirements.txt`, `src/`, `docs/`, `.streamlit/config.toml`
   devem estar na raiz. O `.env`, `secrets.toml` e `brain/` **não** aparecem (estão no `.gitignore`).

> Alternativa sem CLI: se preferir, dá pra fazer tudo pela interface do GitHub, mas o `subtree split`
> é o jeito limpo de manter o histórico.

---

## Passo 2 — Banco Postgres na nuvem (Neon)

1. Crie conta em **neon.tech** (free tier, sem cartão).
2. **Create project** → escolha a região mais próxima (ex: AWS `sa-east-1`, São Paulo).
3. No dashboard, copie a **Connection string**. Ela vem assim:
   ```
   postgresql://usuario:senha@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require
   ```
4. **Ajuste o driver**: troque `postgresql://` por `postgresql+psycopg2://` (o projeto usa psycopg2).
   Guarde essa string — é a sua `DATABASE_URL` de produção.

---

## Passo 3 — Semear o banco do Neon (uma vez)

O gráfico histórico precisa do backfill + backtest no banco. Rode o seed **localmente apontando
para o Neon** (não precisa de Docker aqui):

```bash
cd /caminho/para/o/projeto
export DATABASE_URL="postgresql+psycopg2://usuario:senha@ep-xxxx.../neondb?sslmode=require"
python -m scripts.seed_db
```

Deve imprimir os preços inseridos e ~225 snapshots de risco por stablecoin. Roda uma vez só; o
Neon guarda o dado. (No Windows PowerShell: `$env:DATABASE_URL="..."` antes do `python`.)

---

## Passo 4 — Deploy no Streamlit Community Cloud

1. Crie conta em **share.streamlit.io** e autorize o GitHub.
2. **New app** → selecione o repo `stable-treasury`, branch `main`, arquivo `app.py`.
3. Antes de finalizar, abra **Advanced settings → Secrets** e cole:
   ```toml
   DATABASE_URL = "postgresql+psycopg2://usuario:senha@ep-xxxx.../neondb?sslmode=require"
   ```
   (mesma string do Passo 2/3). O app espelha esse secret para `os.environ` automaticamente
   — ver o shim no topo do `app.py`.
4. **Deploy**. Em ~2-3 min o app sobe num link tipo `https://stable-treasury.streamlit.app`.

---

## Verificação

- Abra o link. O **hero** com a linha de peg do SVB deve aparecer.
- Aba **Risco de Depeg** → selecione USDC → o gráfico histórico com o pico de mar/2023 deve renderizar
  (se aparecer vazio, o seed do Passo 3 não rodou contra o Neon).
- Abas Rail/Liquidity/Compliance funcionam mesmo sem banco (dado ao vivo).

## Notas

- **Cold start (Neon free):** o banco pausa após inatividade; a primeira consulta depois da pausa
  demora alguns segundos a "acordar". Normal no free tier.
- **Segredo:** a `DATABASE_URL` (tem senha) vive **só** nos Secrets do Streamlit Cloud e no seu
  ambiente local — nunca no git. O `.streamlit/secrets.toml` está no `.gitignore`.
- **Atualizações:** cada push no `main` do repo público redeploya o app automaticamente. Para
  sincronizar novas mudanças do monorepo, repita o `subtree split` + push.
