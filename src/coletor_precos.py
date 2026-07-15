import requests
import time
import os
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
ETHERSCAN_URL = "https://api.etherscan.io/api"
POLYGONSCAN_URL = "https://api.polygonscan.com/api"
BCB_SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.10813/dados"
# Order book USDT/BRL (Binance, público, sem key) — microestrutura pro slippage real (ADR-0011)
BINANCE_DEPTH_URL = "https://api.binance.com/api/v3/depth"
# CDI anualizado (série 4389) — referência de cash-equivalent em BRL (ADR-0010)
BCB_CDI_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.4389/dados/ultimos/1"
# T-bill (US Treasury, avg interest rate) — referência de cash-equivalent em USD (ADR-0010)
TREASURY_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"

# Fallbacks das taxas de referência, se as APIs caírem (valores observados em 2026-07-14)
CDI_FALLBACK_PCT = 14.15
TBILL_FALLBACK_PCT = 3.70

# Fallback ÚNICO de câmbio USD/BRL quando a PTAX (BCB SGS) está indisponível.
# Fonte única evita divergência entre módulos (comparador vs otimizador calculavam
# câmbio diferente pro mesmo instante — achado F5 da auditoria 2026-07-14).
PTAX_FALLBACK = 5.7


def preco_stablecoin(moeda: str = "usdt") -> float | None:
    if moeda == "usdt":
        ids = "tether"
    elif moeda == "usdc":
        ids = "usd-coin"
    else:
        return None
    try:
        resp = requests.get(
            COINGECKO_URL,
            params={"ids": ids, "vs_currencies": "brl"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get(ids, {}).get("brl")
    except Exception as e:
        logger.warning(f"Falha ao consultar preço {moeda} via CoinGecko: {e}")
        return None


def gas_fee_eth() -> dict:
    try:
        resp = requests.get(
            ETHERSCAN_URL,
            params={
                "module": "gastracker",
                "action": "gasoracle",
                "apikey": os.environ.get("ETHERSCAN_API_KEY", ""),
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "1":
            result = data["result"]
            return {
                "low_gwei": float(result.get("SafeGasPrice", 0)),
                "avg_gwei": float(result.get("ProposeGasPrice", 0)),
                "high_gwei": float(result.get("FastGasPrice", 0)),
            }
    except Exception as e:
        logger.warning(f"Falha ao consultar Etherscan (fallback 20 gwei ativado): {e}")
    return {"low_gwei": 10, "avg_gwei": 20, "high_gwei": 50}


def gas_fee_polygon() -> dict:
    try:
        resp = requests.get(
            POLYGONSCAN_URL,
            params={
                "module": "gastracker",
                "action": "gasoracle",
                "apikey": os.environ.get("POLYGONSCAN_API_KEY", ""),
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "1":
            result = data["result"]
            return {
                "low_gwei": float(result.get("SafeGasPrice", 0)),
                "avg_gwei": float(result.get("ProposeGasPrice", 0)),
                "high_gwei": float(result.get("FastGasPrice", 0)),
            }
    except Exception as e:
        logger.warning(f"Falha ao consultar PolygonScan (fallback 50 gwei ativado): {e}")
    return {"low_gwei": 30, "avg_gwei": 50, "high_gwei": 100}


def preco_eth() -> float | None:
    try:
        resp = requests.get(
            COINGECKO_URL,
            params={"ids": "ethereum", "vs_currencies": "usd"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("ethereum", {}).get("usd")
    except Exception as e:
        logger.warning(f"Falha ao consultar ETH via CoinGecko: {e}")
        return None


def preco_matic() -> float | None:
    try:
        resp = requests.get(
            COINGECKO_URL,
            params={"ids": "matic-network", "vs_currencies": "usd"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("matic-network", {}).get("usd")
    except Exception as e:
        logger.warning(f"Falha ao consultar MATIC via CoinGecko: {e}")
        return None


def order_book_usdt_brl(limit: int = 100) -> dict | None:
    # order book real de USDT/BRL (Binance). Retorna {'bids': [[preco, qty], ...],
    # 'asks': [...]} com floats, ou None se a API falhar. Base do slippage medido (ADR-0011).
    try:
        resp = requests.get(
            BINANCE_DEPTH_URL, params={"symbol": "USDTBRL", "limit": limit}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "bids": [[float(p), float(q)] for p, q in data["bids"]],
            "asks": [[float(p), float(q)] for p, q in data["asks"]],
        }
    except Exception as e:
        logger.warning(f"Falha ao consultar order book USDT/BRL via Binance: {e}")
        return None


@lru_cache(maxsize=1)
def taxa_cdi() -> float:
    # CDI anualizado (% a.a.) — referência de rendimento de cash-equivalent em BRL.
    try:
        resp = requests.get(BCB_CDI_URL, params={"formato": "json"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            return float(data[-1]["valor"])
    except Exception as e:
        logger.warning(f"Falha ao consultar CDI via BCB SGS (fallback {CDI_FALLBACK_PCT}%): {e}")
    return CDI_FALLBACK_PCT


@lru_cache(maxsize=1)
def taxa_tbill() -> float:
    # T-bill (% a.a.) — referência de rendimento de cash-equivalent em USD.
    try:
        resp = requests.get(
            TREASURY_URL,
            params={
                "filter": "security_desc:eq:Treasury Bills",
                "sort": "-record_date",
                "page[size]": "1",
            },
            timeout=10,
        )
        resp.raise_for_status()
        registros = resp.json().get("data", [])
        if registros:
            return float(registros[0]["avg_interest_rate_amt"])
    except Exception as e:
        logger.warning(f"Falha ao consultar T-bill via US Treasury (fallback {TBILL_FALLBACK_PCT}%): {e}")
    return TBILL_FALLBACK_PCT


@lru_cache(maxsize=1)
def ptax_venda() -> float | None:
    try:
        from datetime import datetime, timedelta
        hoje = datetime.now()
        inicio = (hoje - timedelta(days=7)).strftime("%d/%m/%Y")
        fim = hoje.strftime("%d/%m/%Y")
        resp = requests.get(
            BCB_SGS_URL,
            params={"formato": "json", "dataInicial": inicio, "dataFinal": fim},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            return float(data[-1]["valor"])
    except Exception as e:
        logger.warning(f"Falha ao consultar PTAX via BCB SGS: {e}")
    return None
