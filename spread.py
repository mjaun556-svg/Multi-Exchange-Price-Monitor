"""
spread.py
---------
Compares prices across exchanges and calculates spread metrics.

Key concepts:
  - Spread (absolute):  highest_price - lowest_price
  - Spread (%):         (spread / lowest_price) × 100
  - Arbitrage route:    buy on cheapest exchange, sell on most expensive

Note on real arbitrage:
  Even if a spread looks profitable, real arbitrage must account for:
    - Trading fees (typically 0.05%–0.1% per side = 0.1–0.2% round trip)
    - Withdrawal/transfer fees between exchanges
    - Transfer time (price may move before you can close the other leg)
  A spread < 0.2–0.3% is rarely profitable in practice.
"""

from dataclasses import dataclass
from typing import Optional
from src.fetchers import PriceQuote


@dataclass
class SpreadResult:
    """Holds the full spread analysis for one polling cycle."""
    symbol:            str
    quotes:            list            # list of PriceQuote, sorted by price
    cheapest:          PriceQuote
    most_expensive:    PriceQuote
    spread_abs:        float           # price difference in USD
    spread_pct:        float           # percentage spread
    mid_price:         float           # simple average of all prices
    is_alert:          bool            # True if spread > alert threshold
    alert_threshold:   float           # the configured threshold (%)


def analyse_spreads(
    quotes: list,
    symbol: str,
    alert_threshold: float = 0.10,
) -> Optional[SpreadResult]:
    """
    Compare prices across all exchanges and compute spread metrics.

    Args:
        quotes:           List of PriceQuote objects from fetch_all()
        symbol:           Trading pair string (for labelling)
        alert_threshold:  Spread % that triggers an alert (default: 0.10%)

    Returns:
        SpreadResult, or None if fewer than 2 quotes are available.
    """
    if len(quotes) < 2:
        return None

    # Sort quotes cheapest → most expensive
    sorted_quotes = sorted(quotes, key=lambda q: q.price)

    cheapest       = sorted_quotes[0]
    most_expensive = sorted_quotes[-1]

    spread_abs = most_expensive.price - cheapest.price
    spread_pct = (spread_abs / cheapest.price) * 100

    mid_price  = sum(q.price for q in quotes) / len(quotes)

    return SpreadResult(
        symbol          = symbol,
        quotes          = sorted_quotes,
        cheapest        = cheapest,
        most_expensive  = most_expensive,
        spread_abs      = round(spread_abs, 4),
        spread_pct      = round(spread_pct, 6),
        mid_price       = round(mid_price, 4),
        is_alert        = spread_pct >= alert_threshold,
        alert_threshold = alert_threshold,
    )
