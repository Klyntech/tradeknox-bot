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
- Fallback: Oracle Cloud always-free VPS if needed

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

## Repo Visibility: Public (temporary)

- Can't create private repo without GitHub org
- Code isn't secret — strategy is in the execution
- Make private later once org is created
