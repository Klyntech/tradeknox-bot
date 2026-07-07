# TradeKnox

SMC-based trading signal bot with backtested strategies, Stripe subscriptions, and tiered access.

## Documentation

Full documentation in [`docs/`](docs/README.md):
- [Getting Started](docs/01-getting-started.md)
- [Architecture](docs/02-architecture.md)
- [Strategies](docs/03-strategies.md)
- [Scoring System](docs/04-scoring-system.md)
- [Risk Management](docs/05-risk-management.md)
- [Signal Pipeline](docs/06-signal-pipeline.md)
- [Deployment](docs/07-deployment.md)
- [Revenue Model](docs/08-revenue-model.md)
- [Decisions](docs/09-decisions.md)
- [Backtest Report](docs/10-backtest-report.md)
- [API Reference](docs/11-api-reference.md)
- [Troubleshooting](docs/12-troubleshooting.md)
- [Changelog](docs/13-changelog.md)

## What It Does

Scans XAUUSD and GBPJPY using Smart Money Concepts — market structure, order blocks, fair value gaps, Fibonacci — scores setups against a weighted confidence system, and sends formatted signals to a private Telegram channel.

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | 3 signals/day, 15 min delay |
| Pro | $29/mo | Unlimited signals, instant delivery |
| VIP | $49/mo | Signals + risk management + course |

## Architecture

```
app.py                        — single-process entry (Flask + Telegram)
├── bot.py                    — orchestrator, scan loop, signal pipeline
│   ├── data_layer.py         — price feeds, indicators (ATR, RSI, EMA, RVOL)
│   ├── market_structure.py   — trend, BOS/CHoCH, liquidity zones
│   ├── entry_logic.py        — order blocks, FVGs, Fibonacci, candle patterns
│   ├── strategies.py         — per-pair backtested strategies (MA, RSI, Breakout)
│   ├── scoring_engine.py     — weighted scoring (0-20), risk management
│   └── signal_output.py      — Telegram formatting, SQLite trade log
├── commands.py               — /start, /subscribe, /status, /stats, /key, /help
├── stripe_webhook.py         — Stripe Checkout + webhook handling
├── subscriptions.py          — HMAC license key generation + validation
├── user_manager.py           — user registration, tier gating, signal limits
└── config.py                 — all env vars and constants
```

## Signal Pipeline

1. **Session Filter** — only trade during London, NY, or Overlap sessions
2. **News Blackout** — block around high-impact events (when API configured)
3. **Max Trades** — enforce daily and per-session limits
4. **Data Fetch** — OHLCV via yfinance, multi-timeframe (15m, 1h, 4h)
5. **Market Structure** — trend classification, BOS/CHoCH, liquidity zones
6. **Entry Logic** — order blocks, FVGs, Fibonacci, candle confirmation
7. **Indicators** — RSI signal/divergence, EMA alignment, volume
8. **Strategy Confluence** — per-pair MA crossover, RSI reversal, breakout
9. **Scoring** — weighted score across 6 categories (max 20 points)
10. **Risk Management** — position sizing, SL/TP, R:R validation
11. **Trade Management** — TP/SL alerts, breakeven moves, performance tracking
12. **Telegram Output** — formatted signals with optional anti-leak delay

## Setup

### Environment Variables

```bash
# Required
TELEGRAM_TOKEN=           # Bot token from @BotFather
PRIVATE_CHANNEL_ID=       # Telegram channel ID for signals
LICENSE_SECRET=           # HMAC key for license signing (Render auto-generates)

# Stripe (required for payments)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=
STRIPE_VIP_PRICE_ID=
DOMAIN=                   # Your Render URL (e.g., https://tradeknox.onrender.com)

# Optional
ACCOUNT_BALANCE=10000     # Account size for risk calculations
PUBLIC_CHANNEL_ID=        # Public channel with 15-min delayed signals
NEWS_API_KEY=             # For news blackout filtering
TRADES_DB_PATH=trades.db
LICENSES_DB_PATH=licenses.db
```

### Local Development

```bash
pip install -r requirements.txt
python app.py
```

### Deploy to Render

1. Push to GitHub
2. Connect repo to Render
3. Render auto-detects `render.yaml` and sets up the service
4. Set env vars in Render dashboard
5. Bot starts on `https://<your-app>.onrender.com`

## Backtested Performance

6-month backtest (Jan–Jul 2026) on XAUUSD + GBPJPY, 4h timeframe:

| Metric | Value |
|--------|-------|
| Total trades | 116 |
| Win rate | 52.6% |
| Avg R:R | 1:1.45 |
| Combined return | +14.84% |
| Max drawdown | 10.6% |
| Min score threshold | 11/20 |

Per-pair configs are in `strategies.py` with day-of-week filters.

## Tech Stack

- Python 3.11+
- python-telegram-bot (async Telegram API)
- Flask (Stripe webhook server)
- Stripe (subscription payments)
- yfinance (market data)
- SQLite (trade + license persistence)
- Render (hosting)

## License

Proprietary — not for redistribution.
