import os

from sqlalchemy import (
    Column, DateTime, MetaData, Numeric, String, Table, create_engine,
)

# fonte ÚNICA do schema (ADR-0005): esta metadata gera as tabelas tanto no
# SQLite em memória (testes) quanto no Postgres (dev/prod), sem SQL duplicado.
metadata = MetaData()

# Tabela 1: dado bruto imutável — série temporal de preço vs. peg.
peg_prices = Table(
    "peg_prices", metadata,
    Column("coingecko_id", String, primary_key=True),   # qual stablecoin (ex: 'usd-coin')
    Column("ts", DateTime(timezone=True), primary_key=True),  # momento da observação (UTC)
    Column("price", Numeric(12, 8), nullable=False),     # preço; decimal exato, 8 casas p/ depeg fino
)
# PK composta (coingecko_id, ts): impede 2 preços do mesmo ativo no mesmo instante.

# Tabela 2: dado derivado — snapshot de risco calculado (recalculável se o modelo muda).
risk_snapshots = Table(
    "risk_snapshots", metadata,
    Column("coingecko_id", String, primary_key=True),
    Column("ts", DateTime(timezone=True), primary_key=True),  # momento do cálculo
    Column("es", Numeric(10, 8), nullable=False),        # Expected Shortfall
    Column("var", Numeric(10, 8), nullable=False),       # Value at Risk
    Column("faixa", String, nullable=False),             # baixo/medio/alto (ADR-0004)
    Column("teto", Numeric(4, 3), nullable=False),       # teto de alocação (0.60/0.30/0.10)
)


def get_engine(url: str | None = None):
    # precedência: argumento explícito > env DATABASE_URL > Postgres local do container.
    resolved = url or os.environ.get("DATABASE_URL") or _default_local_url()
    return create_engine(resolved, future=True)


def _default_local_url() -> str:
    # casa com o docker-compose.yml (usuário/senha/porta/db do container local).
    return "postgresql+psycopg2://treasury:localdev@localhost:5432/stable_treasury"


def init_schema(engine) -> None:
    # create_all é idempotente: cria tabela só se não existir (não apaga dado).
    metadata.create_all(engine)