"""
fetchers.py
-----------
Fetches the latest ticker price for a given symbol from each exchange
using their free, public REST APIs. No API keys required.

Supported exchanges:
  - Binance  → api.binance.com
  - Bybit    → api.bybit.com
  - OKX      → www.okx.com

Each fetcher returns a simple dict:
  {
    "exchange": "Binance",
    "symbol":   "BTC/USDT",
    "price":    67450.12,
    "source":   "https://...",   # the URL used
  }
  or raises a FetchError on failure.
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass


# ── Custom exception ───────────────────────────────────────────────────────────

class FetchError(Exception):
    """Raised when an exchange fetch fails for any reason."""
    pass


# ── Price result container ─────────────────────────────────────────────────────

@dataclass
class PriceQuote:
    exchange: str
    symbol:   str
    price:    float
    url:      str         # endpoint used (helpful for debugging)


# ── Shared HTTP helper ─────────────────────────────────────────────────────────

def _get_json(url: str, timeout: int = 5) -> dict:
    """
    Make a GET request and return parsed JSON.
    Raises FetchError on network issues, bad status, or bad JSON.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 price-monitor/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise FetchError(f"HTTP {resp.status} from {url}")
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        raise FetchError(f"Network error reaching {url}: {e}")
    except json.JSONDecodeError as e:
        raise FetchError(f"Invalid JSON from {url}: {e}")


# ── Exchange-specific fetchers ─────────────────────────────────────────────────

def fetch_binance(symbol: str = "BTCUSDT") -> PriceQuote:
    """
    Fetch latest price from Binance.
    Endpoint: GET /api/v3/ticker/price
    Docs: https://binance-docs.github.io/apidocs/spot/en/#symbol-price-ticker
    """
    url  = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
    data = _get_json(url)

    # Response: { "symbol": "BTCUSDT", "price": "67450.12000000" }
    try:
        price = float(data["price"])
    except (KeyError, ValueError) as e:
        raise FetchError(f"Binance: unexpected response format — {e}")

    return PriceQuote(
        exchange="Binance",
        symbol=symbol.upper(),
        price=price,
        url=url,
    )


def fetch_bybit(symbol: str = "BTCUSDT") -> PriceQuote:
    """
    Fetch latest price from Bybit (V5 API).
    Endpoint: GET /v5/market/tickers
    Docs: https://bybit-exchange.github.io/docs/v5/market/tickers
    """
    url  = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol.upper()}"
    data = _get_json(url)

    # Response: { "result": { "list": [ { "lastPrice": "67451.00", ... } ] } }
    try:
        price = float(data["result"]["list"][0]["lastPrice"])
    except (KeyError, IndexError, ValueError) as e:
        raise FetchError(f"Bybit: unexpected response format — {e}")

    return PriceQuote(
        exchange="Bybit",
        symbol=symbol.upper(),
        price=price,
        url=url,
    )


def fetch_okx(symbol: str = "BTC-USDT") -> PriceQuote:
    """
    Fetch latest price from OKX.
    Endpoint: GET /api/v5/market/ticker
    Note: OKX uses dashes in symbol names (BTC-USDT, not BTCUSDT).
    Docs: https://www.okx.com/docs-v5/en/#rest-api-market-data-get-ticker
    """
    # Auto-convert BTCUSDT → BTC-USDT for OKX format
    okx_symbol = _to_okx_symbol(symbol)
    url  = f"https://www.okx.com/api/v5/market/ticker?instId={okx_symbol}"
    data = _get_json(url)

    # Response: { "data": [ { "last": "67452.1", ... } ] }
    try:
        price = float(data["data"][0]["last"])
    except (KeyError, IndexError, ValueError) as e:
        raise FetchError(f"OKX: unexpected response format — {e}")

    return PriceQuote(
        exchange="OKX",
        symbol=symbol.upper(),
        price=price,
        url=url,
    )


def _to_okx_symbol(symbol: str) -> str:
    """
    Convert standard symbol format to OKX format.
    Examples:
      BTCUSDT  → BTC-USDT
      ETHUSDT  → ETH-USDT
      SOLUSDT  → SOL-USDT
    """
    symbol = symbol.upper()
    # Handle common quote currencies
    for quote in ("USDT", "USDC", "BTC", "ETH"):
        if symbol.endswith(quote):
            base = symbol[: -len(quote)]
            return f"{base}-{quote}"
    # Fallback: return as-is (OKX will return an error which we catch)
    return symbol


# ── Unified fetch dispatcher ───────────────────────────────────────────────────

# Registry: exchange name → fetcher function
EXCHANGE_FETCHERS = {
    "Binance": fetch_binance,
    "Bybit":   fetch_bybit,
    "OKX":     fetch_okx,
}


def fetch_all(symbol: str = "BTCUSDT") -> dict:
    """
    Fetch prices from all registered exchanges in sequence.

    Returns:
        {
          "quotes":  list of PriceQuote (successful fetches),
          "errors":  dict of exchange → error message (failed fetches),
        }
    """
    quotes = []
    errors = {}

    for name, fetcher in EXCHANGE_FETCHERS.items():
        try:
            quote = fetcher(symbol)
            quotes.append(quote)
        except FetchError as e:
            # Don't crash the whole run if one exchange fails
            errors[name] = str(e)

    return {"quotes": quotes, "errors": errors}
