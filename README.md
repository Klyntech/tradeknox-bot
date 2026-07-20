# TradeKnox

SMC-based trading signal bot with backtested strategies and False Breakout detection. 100% free, no subscriptions.

## Documentation

Full documentation in [`docs/`](docs/README.md):
- [Getting Started](docs/01-getting-started.md)
- [Architecture](docs/02-architecture.md)
- [Strategies](docs/03-strategies.md)
- [Risk Management](docs/05-risk-management.md)
- [Deployment](docs/07-deployment.md)
- [Decisions](docs/09-decisions.md)
- [Backtest Report](docs/10-backtest-report.md)
- [Troubleshooting](docs/12-troubleshooting.md)
- [Changelog](docs/13-changelog.md)

## What It Does

Scans 8 forex pairs using Smart Money Concepts — market structure, order blocks, fair value gaps, Fibonacci — and False Breakout Trap reversals. Scores setups against a weighted confidence system and sends formatted signals to a private Telegram channel.

**100% Free. 100% Transparent.**

- Unlimited signals
- Instant delivery
- 8 pairs: XAUUSD, GBPJPY, EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD
- SMC + False Breakout strategies
- Full track record available

## Architecture

```
app.py                        — single-process entry (Flask + Telegram)
├── bot.py                    — orchestrator, scan loop, signal pipeline
│   ├── data_layer.py         — price feeds, indicators (ATR, RSI, EMA, RVOL)
│   ├── market_structure.py   — trend, BOS/CHoCH, liquidity zones
│   ├── entry_logic.py        — order blocks, FVGs, Fibonacci, candle patterns
│   ├── strategies.py         — day-of-week filter
│   ├── false_breakout.py     — false breakout trap detection
│   ├── scoring_engine.py     — weighted scoring (0-20), risk management
│   └── signal_output.py      — Telegram formatting, SQLite trade log
├── commands.py               — /start, /status, /stats, /portfolio, /help
├── health_server.py          — Flask health check endpoint
└── config.py                 — all env vars and constants
```

## Signal Pipeline

1. **Session Filter** — only trade during London, NY, or Overlap sessions
2. **News Blackout** — block around high-impact events (when API configured)
3. **Max Trades** — enforce daily and per-session limits
4. **Data Fetch** — OHLCV via TwelveData/yfinance, multi-timeframe (1h, 4h)
5. **Market Structure** — trend classification, BOS/CHoCH, liquidity zones
6. **Entry Logic** — order blocks, FVGs, Fibonacci, candle confirmation
7. **Indicators** — RSI signal/divergence, EMA alignment, volume
8. **Strategy Confluence** — day-of-week filter
9. **Scoring** — weighted score across 6 categories (max 20 points)
10. **Risk Management** — position sizing, SL/TP, R:R validation
11. **False Breakout Scan** — secondary strategy for ranging markets
12. **Trade Management** — TP/SL alerts, breakeven moves, performance tracking
13. **Telegram Output** — formatted signals with optional anti-leak delay

## Setup

### Environment Variables

```bash
# Required
TELEGRAM_TOKEN=           # Bot token from @BotFather
PRIVATE_CHANNEL_ID=       # Telegram channel ID for signals

# Optional
ACCOUNT_BALANCE=10000     # Account size for risk calculations
PUBLIC_CHANNEL_ID=        # Public channel with delayed signals
NEWS_API_KEY=             # For news blackout filtering
TWELVEDATA_API_KEY=       # Primary data source (falls back to yfinance)
SENTRY_DSN=               # Error tracking (optional)
TRADES_DB_PATH=trades.db  # Database path
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

## Tech Stack

- Python 3.11+
- python-telegram-bot (async Telegram API)
- Flask (health check server)
- TwelveData / yfinance (market data)
- SQLite (trade persistence)
- Sentry (error tracking)
- Render (hosting)

## License

Proprietary — not for redistribution.
