"""
logger.py
---------
Saves every polling cycle to logs/prices.csv.

Why log?
  - Chart spread over time: does it widen during volatility?
  - Find which exchange is consistently cheapest
  - Build a dataset to test arbitrage strategies
  - Understand exchange latency patterns
"""

import csv
import os
from datetime import datetime

from src.spread import SpreadResult

LOG_DIR  = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "prices.csv")

HEADERS = [
    "timestamp", "symbol", "cycle",
    "binance_price", "bybit_price", "okx_price",
    "spread_abs", "spread_pct", "mid_price",
    "cheapest_exchange", "priciest_exchange", "alert",
]


def init_logger():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        with open(LOG_FILE, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=HEADERS).writeheader()


def log_cycle(result: SpreadResult, cycle: int):
    """Append one row per polling cycle to the CSV log."""
    # Build a quick lookup: exchange name → price
    price_map = {q.exchange: q.price for q in result.quotes}

    row = {
        "timestamp":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol":             result.symbol,
        "cycle":              cycle,
        "binance_price":      price_map.get("Binance", ""),
        "bybit_price":        price_map.get("Bybit",   ""),
        "okx_price":          price_map.get("OKX",     ""),
        "spread_abs":         result.spread_abs,
        "spread_pct":         result.spread_pct,
        "mid_price":          result.mid_price,
        "cheapest_exchange":  result.cheapest.exchange,
        "priciest_exchange":  result.most_expensive.exchange,
        "alert":              result.is_alert,
    }
    with open(LOG_FILE, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=HEADERS).writerow(row)
