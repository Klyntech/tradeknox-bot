# TradeKnox Documentation

Everything you need to understand, run, and modify TradeKnox.

## Quick Links

| Doc | What It Covers |
|-----|----------------|
| [01 - Getting Started](01-getting-started.md) | Clone, install, run locally, first signal |
| [02 - Architecture](02-architecture.md) | File structure, data flow, dependencies |
| [03 - Strategies](03-strategies.md) | All 8 strategies, parameters, backtest results |
| [04 - Scoring System](04-scoring-system.md) | How scoring works (0-20 points) |
| [05 - Risk Management](05-risk-management.md) | SL/TP, position sizing, R:R |
| [06 - Signal Pipeline](06-signal-pipeline.md) | 12-layer pipeline explained |
| [07 - Deployment](07-deployment.md) | Render setup + env vars |
| [08 - Revenue Model](08-revenue-model.md) | Tiers, pricing, payment flow |
| [09 - Decisions](09-decisions.md) | All decisions with rationale |
| [10 - Backtest Report](10-backtest-report.md) | Full 3.5-year backtest results |
| [11 - API Reference](11-api-reference.md) | Bot commands + webhook endpoints |
| [12 - Troubleshooting](12-troubleshooting.md) | Common issues + fixes |
| [13 - Changelog](13-changelog.md) | Version history |

## What Is TradeKnox?

A Telegram trading signal bot that scans XAUUSD, GBPJPY, and USDJPY using Smart Money Concepts, backtested strategies, and a weighted scoring system. Sends formatted signals to a private Telegram channel with tiered access (Free/Pro/VIP).

## Tech Stack

- Python 3.11+
- python-telegram-bot (async Telegram API)
- Flask (Stripe webhook server)
- Stripe (subscription payments)
- yfinance (market data)
- matplotlib + Pillow (chart generation)
- SQLite (trade + license persistence)
- Render (hosting)

## Current Status

- Bot: Complete (12-layer signal pipeline)
- Landing page: Complete (React + Tailwind)
- Strategies: 8 backtested (3.5 years data)
- Payment: Stripe (blocked — user is 17, needs alternative)
- Deployment: Ready (needs Telegram bot token)

## Blockers

1. **Telegram bot token** — phone unavailable
2. **Payment processor** — Stripe not available in Nigeria, user is 17
3. **Deploy to Render** — needs Telegram + payment credentials
