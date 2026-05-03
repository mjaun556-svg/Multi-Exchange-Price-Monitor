"""
test_monitor.py
---------------
Unit tests for spread analysis and fetcher utilities.

Run with:  python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fetchers import PriceQuote, _to_okx_symbol
from src.spread   import analyse_spreads, SpreadResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_quotes(prices: dict) -> list:
    """Build a list of PriceQuotes from {exchange: price} dict."""
    return [
        PriceQuote(exchange=ex, symbol="BTCUSDT", price=p, url="")
        for ex, p in prices.items()
    ]


# ── OKX symbol conversion ─────────────────────────────────────────────────────

def test_okx_symbol_btcusdt():
    assert _to_okx_symbol("BTCUSDT") == "BTC-USDT"

def test_okx_symbol_ethusdt():
    assert _to_okx_symbol("ETHUSDT") == "ETH-USDT"

def test_okx_symbol_solusdt():
    assert _to_okx_symbol("SOLUSDT") == "SOL-USDT"

def test_okx_symbol_lowercase():
    assert _to_okx_symbol("btcusdt") == "BTC-USDT"


# ── Spread calculation ────────────────────────────────────────────────────────

def test_spread_correct_values():
    """Spread maths should be accurate."""
    quotes = make_quotes({"Binance": 67_450.0, "Bybit": 67_455.0, "OKX": 67_460.0})
    result = analyse_spreads(quotes, "BTCUSDT")

    # Cheapest = Binance, most expensive = OKX
    assert result.cheapest.exchange      == "Binance"
    assert result.most_expensive.exchange == "OKX"
    assert result.spread_abs             == 10.0
    expected_pct = (10.0 / 67_450.0) * 100
    assert abs(result.spread_pct - expected_pct) < 1e-4


def test_spread_two_exchanges():
    """Works correctly with only two exchanges."""
    quotes = make_quotes({"Binance": 100.0, "Bybit": 100.5})
    result = analyse_spreads(quotes, "BTCUSDT")
    assert result.spread_abs == 0.5
    assert abs(result.spread_pct - 0.5) < 1e-4


def test_mid_price():
    """Mid price = simple average of all exchange prices."""
    quotes = make_quotes({"Binance": 100.0, "Bybit": 102.0, "OKX": 104.0})
    result = analyse_spreads(quotes, "BTCUSDT")
    assert abs(result.mid_price - 102.0) < 1e-4


def test_quotes_sorted_cheapest_first():
    """Quotes should be sorted cheapest → most expensive."""
    quotes = make_quotes({"OKX": 300.0, "Binance": 100.0, "Bybit": 200.0})
    result = analyse_spreads(quotes, "BTCUSDT")
    prices = [q.price for q in result.quotes]
    assert prices == sorted(prices)


# ── Alert logic ───────────────────────────────────────────────────────────────

def test_alert_triggered():
    """Alert should fire when spread exceeds threshold."""
    quotes = make_quotes({"Binance": 100.0, "Bybit": 100.5})
    # spread = 0.5%, threshold = 0.3% → should alert
    result = analyse_spreads(quotes, "BTCUSDT", alert_threshold=0.3)
    assert result.is_alert is True


def test_alert_not_triggered():
    """Alert should not fire when spread is below threshold."""
    quotes = make_quotes({"Binance": 100.0, "Bybit": 100.05})
    # spread ≈ 0.05%, threshold = 0.10% → no alert
    result = analyse_spreads(quotes, "BTCUSDT", alert_threshold=0.10)
    assert result.is_alert is False


def test_alert_exact_threshold():
    """Alert should fire when spread exactly equals threshold."""
    # spread = 0.10%, threshold = 0.10% → should alert (≥ not >)
    quotes = make_quotes({"Binance": 100.0, "Bybit": 100.10})
    result = analyse_spreads(quotes, "BTCUSDT", alert_threshold=0.10)
    assert result.is_alert is True


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_insufficient_quotes_returns_none():
    """analyse_spreads needs at least 2 quotes."""
    quotes = make_quotes({"Binance": 67_450.0})
    result = analyse_spreads(quotes, "BTCUSDT")
    assert result is None


def test_zero_quotes_returns_none():
    result = analyse_spreads([], "BTCUSDT")
    assert result is None


def test_equal_prices_zero_spread():
    """When all exchanges show the same price, spread is 0."""
    quotes = make_quotes({"Binance": 500.0, "Bybit": 500.0, "OKX": 500.0})
    result = analyse_spreads(quotes, "BTCUSDT")
    assert result.spread_abs == 0.0
    assert result.spread_pct == 0.0
    assert result.is_alert   is False
