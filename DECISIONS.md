# Decisions

## Brand: TradeKnox

- Chosen over "SignalKnox" — preferred the name
- Verified available: no GitHub, Telegram, or web matches
- Short, memorable, trading-focused

## Base Repo: trading_signal_bot

- 11 files, fully working, standalone
- Simpler than MarketMate (571 files) or jarvis (662 files)
- Decision: enhance this repo, not rebuild from noventra

## Revenue Model: Abandoned (Bot is now Free)

- All strategies and signals are 100% free
- No payment processor needed
- Focus on building the best signal bot, not monetization

## Hosting: Render Free Tier

- Free web service, auto-deploys from GitHub
- Sleeps after 15 min inactivity — mitigated by UptimeRobot ping
- Single-process deployment: Flask (webhooks) + Telegram (bot) in one process

## Data Source: Twelve Data (primary) + yfinance (fallback)

- Twelve Data: 800 calls/day free tier
- Auto-fallback to yfinance on rate limit / error
- Symbol mapping for all 8 pairs on both sources

## Strategy Approach: Pipeline-Based, Not Indicator-Based

- All 8 indicator-based strategies deleted (MarketMate Graveyard)
- Replaced by 2 validated strategies:
  1. **SMC 8-Gate** — Sequential fail-fast pipeline (8 gates, PF 3.65)
  2. **False Breakout Trap** — Failed breakout detection (PF 2.39 on GBPUSD)

- False Breakout discovered via brainstorming (Jul 10, 2026)
  - Simple rule: price exceeds swing high/low but closes back within 2 bars → reversal
  - Survived 6/6 adversarial tests on all 5 validated pairs
  - 0.0% bootstrap probability of PF < 1.0
  - Complements SMC 8-Gate: works in RANGING where SMC is weaker

## Symbols: 8 Pairs

- EURUSD, GBPUSD, USDJPY, XAUUSD, AUDUSD, NZDUSD, USDCAD, GBPJPY
- All 8 actively scanned and traded
- 20+ years of data per pair

## Scoring Engine: Simplified

- Strategy confluence score always 0 (no indicator strategies to confluate)
- SMC 8-Gate gates determine signal quality directly

## False Breakout: Regime-Agnostic

- Works in ALL market regimes (PF > 1.4 in every regime)
- No regime filter needed — deploy as secondary scanner to SMC 8-Gate

## Repo Visibility: Public

- Code isn't secret — strategy is in the execution
- Make private later once GitHub org is created
