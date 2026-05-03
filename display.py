"""
display.py
----------
All terminal output and formatting lives here.

Keeps main.py and business logic clean — everything visual is in this file.
"""

from datetime import datetime
from src.fetchers import PriceQuote
from src.spread   import SpreadResult


# ── ANSI colours ──────────────────────────────────────────────────────────────
# Work on macOS, Linux, and Windows 10+ terminals

GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"
BLINK   = "\033[5m"

W = 58   # Terminal line width


def _line(char="─"):
    print(char * W)


def print_banner(symbol: str, interval: int, threshold: float):
    """One-time startup banner."""
    print(f"""
{BOLD}{CYAN}
  ╔════════════════════════════════════════════════════╗
  ║   Multi-Exchange Price Monitor                     ║
  ║   Real-time spread & arbitrage tracker             ║
  ╚════════════════════════════════════════════════════╝
{RESET}
  {DIM}Symbol    : {BOLD}{symbol.upper()}{RESET}
  {DIM}Interval  : every {interval}s{RESET}
  {DIM}Alert at  : spread ≥ {threshold}%{RESET}
  {DIM}Exchanges : Binance · Bybit · OKX{RESET}

  {DIM}Press Ctrl+C to stop.{RESET}
""")


def print_cycle_header(cycle: int):
    """Print a timestamped header at the start of each polling cycle."""
    now = datetime.now().strftime("%H:%M:%S")
    _line("═")
    print(f"  {BOLD}Cycle #{cycle:<4}{RESET}  {DIM}{now}{RESET}")
    _line()


def print_prices(result: SpreadResult, errors: dict):
    """
    Print a price table — one row per exchange.
    Cheapest highlighted green, most expensive highlighted red.
    """
    print(f"\n  {BOLD}{'Exchange':<12}  {'Price (USDT)':>16}  {'vs Mid':>10}{RESET}")
    _line()

    for quote in result.quotes:
        # Colour: green = cheapest, red = most expensive, normal = middle
        if quote.exchange == result.cheapest.exchange:
            color = GREEN
            tag   = " ← cheapest"
        elif quote.exchange == result.most_expensive.exchange:
            color = RED
            tag   = " ← most expensive"
        else:
            color = ""
            tag   = ""

        # Deviation from mid price (+ means above mid, - means below)
        diff = quote.price - result.mid_price
        diff_str = f"{diff:+.4f}"

        print(
            f"  {color}{BOLD}{quote.exchange:<12}{RESET}"
            f"  {color}{quote.price:>16,.4f}{RESET}"
            f"  {DIM}{diff_str:>10}{RESET}"
            f"{DIM}{tag}{RESET}"
        )

    # Print any failed exchanges
    for exchange, err in errors.items():
        print(f"  {DIM}{exchange:<12}  {'[FETCH ERROR]':>16}  {err[:22]}{RESET}")

    print()


def print_spread(result: SpreadResult):
    """
    Print the spread analysis block.
    Includes a visual bar showing how wide the spread is.
    """
    spread_color = (
        RED    if result.spread_pct >= result.alert_threshold else
        YELLOW if result.spread_pct >= result.alert_threshold * 0.5 else
        GREEN
    )

    print(f"  {BOLD}Spread Analysis{RESET}")
    _line()
    print(f"  {'Route':<22}  Buy {result.cheapest.exchange} → Sell {result.most_expensive.exchange}")
    print(f"  {'Spread (absolute)':<22}  {spread_color}{result.spread_abs:>10,.4f} USDT{RESET}")
    print(f"  {'Spread (%)':<22}  {spread_color}{result.spread_pct:>10,.6f}%{RESET}")
    print(f"  {'Mid Price':<22}  {result.mid_price:>10,.4f} USDT")

    # Visual bar: shows spread magnitude (max bar = 1.0%)
    bar_fill  = min(int((result.spread_pct / 1.0) * 30), 30)
    bar_empty = 30 - bar_fill
    bar       = f"{spread_color}{'█' * bar_fill}{RESET}{'░' * bar_empty}"
    print(f"\n  0%  [{bar}]  1.0%")
    print(f"       spread = {spread_color}{result.spread_pct:.4f}%{RESET}\n")


def print_alert(result: SpreadResult):
    """Print a prominent alert when spread crosses the threshold."""
    if not result.is_alert:
        return

    print(f"""
  {BOLD}{YELLOW}{'▓' * W}
  ⚡  SPREAD ALERT  ⚡
  {result.spread_pct:.4f}% spread detected on {result.symbol}
  Buy  on {result.cheapest.exchange:<10} @ {result.cheapest.price:,.4f}
  Sell on {result.most_expensive.exchange:<10} @ {result.most_expensive.price:,.4f}
  Profit per unit (before fees): {result.spread_abs:,.4f} USDT
  {'▓' * W}{RESET}
""")


def print_errors(errors: dict):
    """Print fetch errors in a non-alarming way (just informational)."""
    if not errors:
        return
    for exchange, msg in errors.items():
        print(f"  {DIM}⚠  {exchange}: {msg}{RESET}")
    print()


def print_only_one_exchange():
    """Warn when fewer than 2 exchanges responded."""
    print(f"\n  {YELLOW}⚠  Only 1 exchange responded — cannot calculate spread.{RESET}\n")


def print_shutdown(cycles: int, alerts: int):
    """Print a summary when the user hits Ctrl+C."""
    print(f"""
{DIM}
  ──────────────────────────────────────────────
  Session ended.
  Total cycles : {cycles}
  Spread alerts: {alerts}
  ──────────────────────────────────────────────
{RESET}""")
