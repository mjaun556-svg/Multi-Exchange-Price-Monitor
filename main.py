"""
main.py
-------
Multi-Exchange Price Monitor — Entry Point

Polls Binance, Bybit, and OKX at a configurable interval, compares
prices, calculates the spread, and fires an alert when the spread
crosses a threshold you set.

Usage:
  python main.py                              # BTC/USDT, 10s interval, 0.10% alert
  python main.py --symbol ETHUSDT            # track ETH
  python main.py --interval 5                # poll every 5 seconds
  python main.py --threshold 0.05            # alert at 0.05% spread
  python main.py --symbol SOLUSDT --no-log   # skip CSV logging
  python main.py --cycles 20                 # stop after 20 cycles

No API keys required — all endpoints are public.
"""

import time
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.fetchers import fetch_all
from src.spread   import analyse_spreads
from src.display  import (
    print_banner, print_cycle_header, print_prices,
    print_spread, print_alert, print_errors,
    print_only_one_exchange, print_shutdown,
)
from src.logger   import init_logger, log_cycle


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Real-time multi-exchange crypto price monitor with spread alerts"
    )
    parser.add_argument("--symbol",    type=str,   default="BTCUSDT",
                        help="Trading pair (default: BTCUSDT)")
    parser.add_argument("--interval",  type=int,   default=10,
                        help="Polling interval in seconds (default: 10)")
    parser.add_argument("--threshold", type=float, default=0.10,
                        help="Spread %% that triggers an alert (default: 0.10)")
    parser.add_argument("--cycles",    type=int,   default=0,
                        help="Stop after N cycles; 0 = run forever (default: 0)")
    parser.add_argument("--no-log",    action="store_true",
                        help="Disable CSV logging")
    return parser.parse_args()


# ── Main loop ──────────────────────────────────────────────────────────────────

def main():
    args       = parse_args()
    symbol     = args.symbol.upper()
    interval   = args.interval
    threshold  = args.threshold
    max_cycles = args.cycles
    enable_log = not args.no_log

    if enable_log:
        init_logger()

    print_banner(symbol, interval, threshold)

    cycle_count = 0
    alert_count = 0

    while True:
        # Check cycle limit
        if max_cycles > 0 and cycle_count >= max_cycles:
            break

        cycle_count += 1
        print_cycle_header(cycle_count)

        # ── Fetch prices from all exchanges ────────────────────────────────────
        result_raw = fetch_all(symbol)
        quotes = result_raw["quotes"]
        errors = result_raw["errors"]

        # Print any fetch errors (informational, not fatal)
        print_errors(errors)

        # ── Need at least 2 exchanges to compare ───────────────────────────────
        if len(quotes) < 2:
            print_only_one_exchange()
            time.sleep(interval)
            continue

        # ── Analyse spreads ────────────────────────────────────────────────────
        spread_result = analyse_spreads(quotes, symbol, alert_threshold=threshold)

        # ── Display ────────────────────────────────────────────────────────────
        print_prices(spread_result, errors)
        print_spread(spread_result)

        # Fire alert if spread crosses threshold
        if spread_result.is_alert:
            alert_count += 1
            print_alert(spread_result)

        # ── Log to CSV ─────────────────────────────────────────────────────────
        if enable_log:
            log_cycle(spread_result, cycle_count)

        # ── Wait before next cycle ─────────────────────────────────────────────
        time.sleep(interval)

    print_shutdown(cycle_count, alert_count)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Stopped by user.\n")
