# 📡 Multi-Exchange Price Monitor

A real-time crypto price tracker that pulls live quotes from **Binance, Bybit, and OKX** simultaneously, compares them, and alerts you when the spread between exchanges crosses a threshold you set.

No API keys. No heavy libraries. Just Python.

---

## 🤔 Why Do Prices Differ Across Exchanges?

You'd think BTC should cost the same everywhere. It mostly does — but never exactly.

Here's why small differences always exist:

**Different liquidity pools.** Each exchange has its own set of buyers and sellers. When demand spikes on Binance but hasn't yet reached Bybit, the price temporarily diverges.

**Different fee structures.** Maker/taker fees vary by exchange. This changes what effective price traders are willing to accept, which shifts the orderbook.

**Latency between markets.** Information travels fast, but not instantly. A large trade on one exchange causes a price move that takes seconds (or minutes on smaller platforms) to propagate elsewhere.

**Different user bases.** Korean exchanges historically traded at a premium (the "Kimchi premium"). US-based exchanges can price differently during US market hours. Geographic and regulatory factors matter.

These differences are small on liquid pairs like BTC/USDT — typically 0.01% to 0.15% — but they're real, persistent, and tradeable.

---

## ⚡ What Is Arbitrage?

Arbitrage is the practice of buying an asset on one exchange and selling it on another to profit from a price difference.

**Simple example:**
```
BTC price on Binance: $67,450.00
BTC price on OKX:     $67,531.00
Spread:               $81.00  (0.12%)

Action: Buy on Binance, sell on OKX
Gross profit: $81 per BTC
```

**In reality, it's not that simple:**

| Cost | Typical amount |
|------|---------------|
| Taker fee (buy leg) | 0.05% – 0.10% |
| Taker fee (sell leg) | 0.05% – 0.10% |
| Withdrawal fee | varies by coin |
| Transfer time | 10 min – 2 hrs |

A round-trip costs roughly **0.10% – 0.20%** in fees alone. So a 0.12% spread is not profitable — the fees eat it. You need spreads above **0.25–0.30%** to consider it viable, and even then transfer time means the window may close before you complete both legs.

Professionals solve this by pre-funding accounts on both exchanges and doing **simultaneous** buys and sells — eliminating transfer risk entirely.

This project helps you **observe and log** these spreads so you can understand how often actionable opportunities actually occur.

---

## 🌍 Real-World Relevance

| Trader type | How this helps |
|-------------|---------------|
| Retail traders | Understand why your fill on one exchange differs from another |
| Algo traders | First step to building a live arbitrage execution system |
| Quants | Log spread data to backtest cross-exchange strategies |
| Risk managers | Track whether exchange prices are dislocating (sign of stress) |

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/multi-exchange-price-monitor.git
cd multi-exchange-price-monitor
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
# Default: BTCUSDT, poll every 10s, alert at 0.10% spread
python main.py

# Track Ethereum
python main.py --symbol ETHUSDT

# Poll every 5 seconds
python main.py --interval 5

# Alert only when spread exceeds 0.05%
python main.py --threshold 0.05

# Run for exactly 30 cycles then stop
python main.py --cycles 30

# Don't save to CSV
python main.py --no-log
```

---

## 📺 Sample Output

```
╔════════════════════════════════════════════════════╗
║   Multi-Exchange Price Monitor                     ║
║   Real-time spread & arbitrage tracker             ║
╚════════════════════════════════════════════════════╝

  Symbol    : BTCUSDT
  Interval  : every 10s
  Alert at  : spread ≥ 0.10%
  Exchanges : Binance · Bybit · OKX

══════════════════════════════════════════════════════════
  Cycle #1    14:33:07
──────────────────────────────────────────────────────────

  Exchange      Price (USDT)      vs Mid
──────────────────────────────────────────────────────────
  Binance          67,450.1200     -0.8600  ← cheapest
  Bybit            67,451.8000     +0.8200
  OKX              67,452.4500     +1.4700  ← most expensive

  Spread Analysis
──────────────────────────────────────────────────────────
  Route                   Buy Binance → Sell OKX
  Spread (absolute)             2.3300 USDT
  Spread (%)                  0.003455%
  Mid Price                67,451.4567 USDT

  0%  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  1.0%
       spread = 0.0035%

══════════════════════════════════════════════════════════

  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  ⚡  SPREAD ALERT  ⚡
  0.1234% spread detected on BTCUSDT
  Buy  on Binance    @ 67,380.0000
  Sell on OKX        @ 67,463.1200
  Profit per unit (before fees): 83.1200 USDT
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

---

## 📁 Project Structure

```
multi-exchange-price-monitor/
│
├── main.py                  # Entry point: polling loop + CLI args
│
├── src/
│   ├── fetchers.py          # Exchange API handlers (Binance, Bybit, OKX)
│   ├── spread.py            # Price comparison & spread calculation
│   ├── display.py           # All terminal formatting & colour output
│   └── logger.py            # CSV logger → logs/prices.csv
│
├── tests/
│   └── test_monitor.py      # 12 unit tests
│
├── logs/
│   └── prices.csv           # Auto-created at runtime (gitignored)
│
├── requirements.txt         # Only pytest needed
├── .gitignore
└── README.md
```

---

## ⚙️ How It Works

```
Every N seconds:
  │
  ├─ fetch_all(symbol)
  │     ├─ fetch_binance()  → GET api.binance.com/api/v3/ticker/price
  │     ├─ fetch_bybit()    → GET api.bybit.com/v5/market/tickers
  │     └─ fetch_okx()      → GET www.okx.com/api/v5/market/ticker
  │
  ├─ analyse_spreads(quotes, threshold)
  │     ├─ Sort quotes cheapest → most expensive
  │     ├─ spread_abs = max_price - min_price
  │     ├─ spread_pct = spread_abs / min_price × 100
  │     └─ is_alert  = spread_pct >= threshold
  │
  ├─ print_prices()    (colour table)
  ├─ print_spread()    (bar chart + metrics)
  ├─ print_alert()     (if spread > threshold)
  └─ log_cycle()       (CSV row)
```

Each exchange fetcher handles its own error — if one exchange is down, the others continue running.

---

## 🧪 Tests

```bash
python -m pytest tests/ -v
```

Covers: OKX symbol conversion, spread maths, mid-price, sort order, alert thresholds, edge cases (zero spread, one exchange, no exchanges).

---

## ➕ Ideas to Extend

| Extension | Difficulty |
|-----------|------------|
| Add Kraken, Coinbase, Gate.io | ⭐ Easy |
| Telegram / Discord alert on spread spike | ⭐⭐ Medium |
| Plot spread history with matplotlib | ⭐⭐ Medium |
| Track funding rate differences (perps) | ⭐⭐ Medium |
| WebSocket version (sub-second updates) | ⭐⭐⭐ Hard |
| Full arbitrage execution with pre-funded accounts | ⭐⭐⭐⭐ Advanced |

---

## 📦 Dependencies

Zero external libraries for the core code — only Python's standard library.

| Library | Purpose | Version |
|---------|---------|---------|
| `pytest` | Unit testing (optional) | 8.3.5 |

---

## 🔗 APIs Used

| Exchange | Endpoint | Auth required |
|----------|----------|---------------|
| Binance | `/api/v3/ticker/price` | No |
| Bybit | `/v5/market/tickers` | No |
| OKX | `/api/v5/market/ticker` | No |

---

## 📄 License

MIT — use it, extend it, ship it.
