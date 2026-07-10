# TradeKnox

SMC + False Breakout trading signal bot. 8 forex pairs, 2 validated strategies, 100% free.

## Quick Links

- [Strategies](docs/03-strategies.md) — SMC 8-Gate + False Breakout Trap
- [Backtest Report](docs/10-backtest-report.md) — Adversarial validation results
- [Architecture](docs/02-architecture.md) — System design
- [Changelog](docs/13-changelog.md) — Release history

## What It Does

Scans 8 forex pairs using two strategies:
1. **SMC 8-Gate** — Smart Money Concepts pipeline (PF 3.65 on XAUUSD)
2. **False Breakout Trap** — Failed breakout reversal (PF 2.39 on GBPUSD)

Signals are sent instantly to a Telegram channel. 100% free, unlimited signals.

## Architecture

```
app.py                        — single-process entry (Flask + Telegram)
├── bot.py                    — orchestrator, scan loop, signal pipeline
│   ├── data_layer.py         — price feeds (Twelve Data + yfinance)
│   ├── market_structure.py   — trend, BOS/CHoCH, liquidity zones
│   ├── entry_logic.py        — order blocks, FVGs, Fibonacci, candle patterns
│   ├── strategies.py         — day-of-week filter only (indicators deleted)
│   ├── scoring_engine.py     — SMC gate scoring, risk management
│   └── signal_output.py      — Telegram formatting, SQLite trade log
├── commands.py               — Telegram bot commands
├── stripe_webhook.py         — webhook handler
├── subscriptions.py          — license keys
├── user_manager.py           — user gating
└── config.py                 — env vars and constants
```

## Validated Strategies

| Strategy | Type | Best PF | Best Pair | Tests Passed |
|----------|------|---------|-----------|-------------|
| **SMC 8-Gate** | Trend Following | **3.65** | XAUUSD | Full pipeline backtest |
| **False Breakout** | Counter-Trend | **2.39** | GBPUSD | 6/6 adversarial tests |

## Pairs (8)

EURUSD, GBPUSD, USDJPY, XAUUSD, AUDUSD, NZDUSD, USDCAD, GBPJPY

## Research Lab

All strategy development happens in `research/`:
- `brainstorm_test.py` — Test new ideas (5 tested, 1 passed)
- `adversarial_false_breakout.py` — Full adversarial validation
- `gap_backtest.py` — Gap strategy tests (MM-002/MM-012)
- `fast_backtest.py` — Vectorized SMC pipeline backtester
- `data/` — Historical OHLCV for all 8 pairs (20+ years)

## Current Status

### Done
- [x] SMC 8-Gate pipeline (PF 3.65)
- [x] False Breakout Trap discovery (PF 2.39, 6/6 adversarial)
- [x] 8 pairs with 20+ years of historical data
- [x] Full adversarial validation framework
- [x] Bot deployed and live on Render
- [x] All docs updated with current strategies

### Next
- [ ] Integrate False Breakout into bot as secondary scanner
- [ ] Test dual-strategy portfolio performance
- [ ] Add regime-gated deployment (SMC for trending, False Breakout for ranging)
