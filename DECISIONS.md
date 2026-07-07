# Decisions

## Brand: TradeKnox

- Chosen over "SignalKnox" — preferred the name
- Verified available: no GitHub, Telegram, or web matches
- Short, memorable, trading-focused

## Base Repo: trading_signal_bot

- 11 files, fully working, standalone
- Simpler than MarketMate (571 files) or jarvis (662 files)
- Noventra-core has more gates but adds complexity without benefit yet
- Decision: enhance this repo, not rebuild from noventra

## Revenue Model: Subscription + Course

- Free: 3 signals/day, 15 min delay (acquisition funnel)
- Pro: $29/mo — unlimited signals, instant
- VIP: $49/mo — signals + risk mgmt + course
- Course: $39 one-time on Gumroad

## Payment Processor: Stripe

- Professional, subscription-native
- Webhook-based — no polling
- Supports recurring payments
- Personal email acceptable for now

## Hosting: Render Free Tier

- Free web service, auto-deploys from GitHub
- Sleeps after 15 min inactivity — mitigated by UptimeRobot ping
- Single-process deployment: Flask (webhooks) + Telegram (bot) in one process
- Flask runs in background thread, Telegram polling on main thread

## Data Source: yfinance (default)

- Free, no API key needed, covers forex/gold
- Fallback: CCXT for crypto, MetaAPI for live MT4/MT5 data
- Decision: start with yfinance, add MetaAPI later for reliability

## Subscription System: HMAC License Keys

- Server generates license keys with expiry embedded
- Bot validates keys on each scan cycle
- SQLite stores user/tier/key mappings
- Decision: simpler than OAuth, works offline, no external service

## Anti-Leak: Delayed Public Channel

- Private channel gets signals instantly
- Public channel delayed 15 minutes
- Decision: incentivizes paid subscriptions, prevents scraping

## Symbols: XAUUSD + GBPJPY + USDJPY

- Backtested all 5 symbols (XAUUSD, EURUSD, GBPUSD, USDJPY, GBPJPY) on 8 strategies
- 3.5 years of daily data (Jan 2023 — Jul 2026)
- XAUUSD, GBPJPY, USDJPY consistently profitable
- EURUSD, GBPUSD excluded — unprofitable across all strategies
- XAUUSD: PF 2.17 (EMA Crossover), ~18.9%/year
- USDJPY: PF 1.82 (EMA Crossover), ~6.3%/year
- GBPJPY: PF 1.69 (Stochastic Extreme), ~2.0%/year

## Strategy Parameters: Per-Pair Optimization

- XAUUSD: 4h, MA 9/21, Breakout 10, RSI 30/70, EMA 9/21/100
- GBPJPY: 4h, MA 50/200, Breakout 20, RSI 20/80, Stochastic
- USDJPY: 4h, MA 9/21, Breakout 10, RSI 20/80, EMA 9/21/100
- Day-of-week filters added from backtest research
- Confluence score from strategies.py fed into scoring engine

## Score Threshold: 11/20

- Below 11 = no trade (hard gate)
- Requires strategy confluence (min 2 strategies agreeing)
- Tested threshold sensitivity: 11 balanced signal quality vs frequency

## Repo Visibility: Public (temporary)

- Can't create private repo without GitHub org
- Code isn't secret — strategy is in the execution
- Make private later once org is created

## NEWS_API_KEY: Optional

- News filter only active when API key is configured
- Without key, news_clear points not awarded (honest scoring)
- Prevents 2 free points from always-true news check
