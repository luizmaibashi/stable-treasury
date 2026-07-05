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
