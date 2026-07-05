# TradeKnox

SMC-based trading signal bot + education bundle.

## What It Does

Scans forex/gold markets using Smart Money Concepts (market structure, order blocks, fair value gaps, Fibonacci), scores setups against a weighted confidence system, and sends formatted signals to a private Telegram channel.

Free users see 3 signals/day with a 15-minute delay. Pro ($29/mo) and VIP ($49/mo) get instant access.

## Architecture

```
bot.py (orchestrator)
  ├── data_layer.py        — price feeds, indicators (ATR, RSI, EMA, RVOL)
  ├── market_structure.py  — trend, BOS/CHoCH, liquidity zones, premium/discount
  ├── entry_logic.py       — order blocks, FVGs, Fibonacci, candle confirmation
  ├── scoring_engine.py    — weighted scoring (0-17), min threshold gate
  └── signal_output.py     — Telegram formatting, SQLite trade log, performance reports
```

### Signal Pipeline

1. **Data Layer** — fetch OHLCV via yfinance/CCXT, compute indicators
2. **Session Filter** — only trade during London, NY, or Overlap sessions
3. **News Filter** — blackout windows around high-impact events
4. **Market Structure** — detect trend, BOS/CHoCH, liquidity, premium/discount zones
5. **Entry Logic** — find order blocks, FVGs, Fibonacci confluence, candle confirmation
6. **Indicator Confluence** — RSI signal/divergence, EMA bias, volume confirmation
7. **Scoring Engine** — weighted score across 5 categories (max 17 points)
8. **Risk Management** — position sizing, SL/TP calculation, R:R validation
9. **Trade Management** — TP/SL alerts, breakeven moves, performance tracking
10. **Telegram Output** — formatted signal messages with anti-leak delay

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

## Current Goals

- [ ] Deploy working bot to Render
- [ ] Add subscription/license validation
- [ ] Add Telegram bot commands (/start, /subscribe, /status, /stats)
- [ ] Add signal history tracking + win/loss stats
- [ ] Launch public channel @TradeKnoxSignals
- [ ] Create "SMC Trading Blueprint" PDF
- [ ] Publish course on Gumroad
