# TradeKnox

SMC-based trading signal bot + education bundle.

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

Scans XAUUSD and GBPJPY using Smart Money Concepts (market structure, order blocks, fair value gaps, Fibonacci), scores setups against a weighted confidence system, and sends formatted signals to a private Telegram channel.

Free users see 3 signals/day with a 15-minute delay. Pro ($29/mo) and VIP ($49/mo) get instant access.

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

### Signal Pipeline

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

## Coding Standards

- **Python 3.11+** with type hints on all functions
- **Dataclasses** for structured data, not raw dicts
- **Logging** via `logging` module, never `print()`
- **All config** in `config.py` via environment variables
- **SQLite** for trade persistence and subscription tracking
- **Async** Telegram sends with `python-telegram-bot`
- **No hardcoded secrets** — everything via env vars
- **Commit messages** follow conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`

## Revenue Model

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | 3 signals/day, 15 min delay |
| Pro | $29/mo | Unlimited signals, instant delivery |
| VIP | $49/mo | Signals + risk management + course |
| Course | $39 one-time | "SMC Trading Blueprint" PDF on Gumroad |

## Backtested Performance

3.5-year backtest (Jan 2023 — Jul 2026) on 3 pairs, 8 strategies:

| Pair | Best Strategy | Win Rate | Profit Factor | Annual Return |
|------|---------------|----------|---------------|---------------|
| **XAUUSD** | EMA Crossover (MM-008) | 58.0% | **2.17** | ~18.9% |
| **USDJPY** | EMA Crossover (MM-008) | 52.1% | **1.82** | ~6.3% |
| **GBPJPY** | Stochastic Extreme (MM-016) | 54.2% | **1.69** | ~2.0% |

**Strategies:** MA Crossover, Breakout, RSI Extremes, EMA Crossover (MM-008), Heikin Ashi Trend (MM-017), Stochastic Extreme (MM-016), Session Timing, EMA Alignment

**Excluded:** EURUSD, GBPUSD (consistently unprofitable)

Full backtest report: [`docs/10-backtest-report.md`](docs/10-backtest-report.md)

## Current Status

### Done
- [x] Brand selection and repo setup
- [x] Full signal pipeline (12 layers)
- [x] Subscription/license system (HMAC keys)
- [x] Stripe webhook handler (Checkout + 4 webhook events)
- [x] Telegram bot commands (/start, /subscribe, /status, /stats, /key, /help)
- [x] Landing page (React + Tailwind)
- [x] Render deployment config (single-process)
- [x] Backtested strategy research (17 strategies, 5 symbols, 4 timeframes)
- [x] Per-pair optimized strategies with day-of-week filters

### Blocked
- [ ] Telegram bot token (phone unavailable)
- [ ] Stripe account (need API keys + Price IDs)
- [ ] Deploy to Render (needs Telegram + Stripe credentials)

### Next
- [ ] Launch public channel @TradeKnoxSignals
- [ ] Test bot live
- [ ] Launch publicly, post first signals
- [ ] Write "SMC Trading Blueprint" PDF course
- [ ] Publish course on Gumroad ($39)
