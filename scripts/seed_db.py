"""Popula o banco do zero: cria schema, faz backfill histórico (2022→hoje) e gera
os snapshots de risco (backtest). Ponto de entrada único de ingestão (antes não havia).

Uso:
    python -m scripts.seed_db            # usa DATABASE_URL (ou Postgres local do docker-compose)

Requer o banco no ar: `docker compose up -d` (local) ou DATABASE_URL apontando pro Neon.
"""
from src.db import get_engine, init_schema
from src.ingestao import backfill_completo, gerar_snapshots_risco_historico, STABLECOINS_PADRAO


def main() -> None:
    engine = get_engine()
    print("→ criando schema (idempotente)...")
    init_schema(engine)

    print("→ backfill histórico de preço (2022→hoje, DefiLlama)...")
    inseridos = backfill_completo(engine)
    for coin, n in inseridos.items():
        print(f"   {coin}: {n} preços novos")

    print("→ gerando snapshots de risco (backtest, janela deslizante 90d)...")
    for coin in STABLECOINS_PADRAO:
        gerados = gerar_snapshots_risco_historico(engine, coin)
        print(f"   {coin}: {gerados} snapshots de risco")

    print("✓ banco populado. Rode: streamlit run app.py")


if __name__ == "__main__":
    main()
