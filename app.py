import os

import streamlit as st
from dotenv import load_dotenv

from src.db import get_engine
from src.ui import aplicar_estilo, hero
from src.views import (
    comparador,
    compliance,
    configuracao,
    decisao_pre_pagamento,
    liquidez,
    risco_depeg,
)

load_dotenv()

try:
    if not os.environ.get("DATABASE_URL") and "DATABASE_URL" in st.secrets:
        os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]
except Exception:
    pass


@st.cache_resource
def _engine():
    return get_engine()


st.set_page_config(page_title="StableTreasury", page_icon="🏦", layout="wide")

aplicar_estilo()
hero()

tab_risco, tab_liquidez, tab_rails, tab_compliance, tab_decisao, tab_config = st.tabs([
    "📈 Risco de Depeg",
    "💧 Liquidity Optimizer",
    "📊 Rail Comparator",
    "🔒 Compliance Filter",
    "🗂️ Decisão pré-pagamento",
    "⚙️ Config",
])

with tab_risco:
    risco_depeg.renderizar(_engine())
with tab_liquidez:
    liquidez.renderizar()
with tab_rails:
    comparador.renderizar()
with tab_compliance:
    compliance.renderizar()
with tab_decisao:
    decisao_pre_pagamento.renderizar()
with tab_config:
    configuracao.renderizar()
