# 09 — Decisions

Every major decision made during TradeKnox development, with rationale.

---

## Brand: TradeKnox

**Chosen:** TradeKnox  
**Rejected:** SignalKnox, TradeAlert, SignalBot

**Why:**
- Short, memorable (8 characters)
- "Trade" = clear purpose
- "Knox" = sounds strong, secure
- No GitHub, Telegram, or web matches
- Available as domain (tradeknox.com)

---

## Base Repo: trading_signal_bot

**Chosen:** trading_signal_bot (11 files, fully working)  
**Rejected:** MarketMate (571 files), jarvis (662 files), noventra-core

**Why:**
- Simplest codebase — easier to understand and modify
- Already working — no need to rebuild
- Noventra has more gates but adds complexity without benefit yet
- Decision: enhance this repo, not rebuild from scratch

---

## Revenue Model: Subscription + Course

**Chosen:** Free/Pro/VIP tiers + $39 course  
**Rejected:** One-time purchase, donation-based, ad-supported

**Why:**
- Subscription = recurring revenue
- Free tier = acquisition funnel
- Course = standalone product + VIP bonus
- Proven model in trading signal space

---

## Payment Processor: Stripe (Deferred)

**Chosen:** Stripe  
**Status:** BLOCKED — User is 17, Stripe requires 18+  
**Alternative:** Telegram Stars (crypto withdrawal)

**Why Stripe was chosen:**
- Professional, subscription-native
- Webhook-based — no polling
- Supports recurring payments
- Good documentation

**Why it's blocked:**
- User is Nigerian — Stripe not available for Nigerian merchants
- User is 17 — needs 18+ for merchant account
- Alternative: Telegram Stars (works for any age)

---

## Hosting: Render Free Tier

**Chosen:** Render Free Tier  
**Rejected:** Heroku, Railway, VPS

**Why:**
- Free — no cost
- Auto-deploys from GitHub
- Good Python support
- Health endpoint available
- Mitigated sleeping with UptimeRobot

**Trade-off:**
- Sleeps after 15 min inactivity → mitigated by UptimeRobot ping
- Limited resources → single-process deployment works

---

## Data Source: yfinance (default)

**Chosen:** yfinance  
**Rejected:** OANDA, MetaTrader, Alpha Vantage

**Why:**
- Free — no API key needed
- Covers all pairs we need (XAUUSD, GBPJPY, USDJPY)
- Good historical data (3.5+ years)
- Easy to use with Python

**Fallback:** Dukascopy for validation, CCXT for crypto

---

## Subscription System: HMAC License Keys

**Chosen:** HMAC license keys  
**Rejected:** OAuth, JWT, external service

**Why:**
- Simpler than OAuth
- Works offline (no external service)
- Can be validated without network call
- SQLite stores user/tier/key mappings

**How it works:**
1. Server generates key with expiry embedded
2. Key is HMAC-signed (tamper-proof)
3. Bot validates key on each scan cycle
4. SQLite stores user/tier/key mappings

---

## Anti-Leak: Delayed Public Channel

**Chosen:** 15-minute delay for free tier  
**Rejected:** No delay, watermark-only, DRM

**Why:**
- Incentivizes paid subscriptions
- Prevents scraping (signals lose value after 15 min)
- Simple to implement
- Common in trading signal space

---

## Symbols: XAUUSD + GBPJPY + USDJPY

**Chosen:** XAUUSD, GBPJPY, USDJPY  
**Rejected:** EURUSD, GBPUSD, AUDUSD, NZDUSD

**Why:**
- XAUUSD: Highest returns (PF 2.17), most volatile
- GBPJPY: Good for reversals (Stochastic PF 1.69)
- USDJPY: Now profitable with new strategies (PF 1.82)
- EURUSD: Consistently unprofitable across all strategies
- GBPUSD: Mixed results, unreliable

**Backtest evidence:**
- 3.5 years of daily data
- All 5 pairs tested with 8 strategies
- Only 3 pairs consistently profitable

---

## Strategy Parameters: Per-Pair Optimization

**Chosen:** Different parameters per pair  
**Rejected:** One-size-fits-all parameters

**Why:**
- XAUUSD: Volatile, needs wider stops (MA 9/21, Breakout 10)
- GBPJPY: Trending, needs tighter entries (MA 50/200, RSI 20/80)
- USDJPY: Session-dependent, needs EMA confirmation (EMA 9/21/100)

**Evidence:**
- XAUUSD optimal: MA 9/21, Breakout 10, RSI 30/70
- GBPJPY optimal: MA 50/200, Breakout 20, RSI 20/80
- USDJPY optimal: EMA 9/21/100, Breakout 10, RSI 20/80

---

## Score Threshold: 11/20

**Chosen:** 11 out of 20 (55% confidence)  
**Rejected:** 9/20 (too many signals), 13/20 (too few)

**Why:**
- 11/20 balances signal quality vs frequency
- Below 11 = too many false signals
- Above 13 = too few signals (users get bored)
- Tested threshold sensitivity in backtest

**Evidence:**
- At 11/20: ~5-8 signals/day (good)
- At 9/20: ~15-20 signals/day (too many, low quality)
- At 13/20: ~2-3 signals/day (too few, users churn)

---

## Repo Visibility: Public (temporary)

**Chosen:** Public repo  
**Rejected:** Private repo

**Why:**
- Can't create private repo without GitHub org
- Code isn't secret — strategy is in the execution
- Build in public = credibility
- Make private later once org is created

---

## NEWS_API_KEY: Optional

**Chosen:** Optional news API key  
**Rejected:** Required news API

**Why:**
- Prevents bot from crashing if key not set
- Without key, news_clear points = 0 (honest scoring)
- Prevents 2 free points from always-true news check
- Can add later when budget allows

---

## New Strategies: EMA Crossover, Heikin Ashi, Stochastic

**Chosen:** 3 new strategies from MarketMate  
**Rejected:** Keep only original 2 strategies

**Why:**
- Original strategies only worked on XAUUSD + GBPJPY
- New strategies make USDJPY profitable
- More strategies = more signals = more value
- Backtested on 3.5 years of data

**Evidence:**
- EMA Crossover: PF 2.17 on XAUUSD, PF 1.82 on USDJPY
- Heikin Ashi: PF 1.67 on XAUUSD, PF 1.40 on GBPJPY
- Stochastic: PF 1.69 on GBPJPY, PF 1.76 on XAUUSD

---

## Data Sources: yfinance + Dukascopy

**Chosen:** Multiple data sources for validation  
**Rejected:** yfinance only

**Why:**
- Cross-validation ensures data quality
- Dukascopy provides 5+ years of hourly data
- Different sources = different biases
- Strategies that work on both = more robust

---

## Documentation: docs/ folder

**Chosen:** Separate docs/ folder with 13 files  
**Rejected:** Single DOCS.md, inline comments only

**Why:**
- Organized, easy to navigate
- Standard practice for projects
- Can be expanded as project grows
- Links from README.md for discoverability

---

## Future Decisions

### Payment Alternative (When 18+)

**Options:**
1. **Paystack** — Nigeria's #1 gateway, 1.5% + ₦100 fees
2. **Flutterwave** — Pan-African alternative
3. **Telegram Payments API** — Native Telegram integration

**Decision pending:** User needs to turn 18 or find alternative.

### Additional Pairs

**Potential:** AUDUSD, NZDUSD, EURGBP  
**Status:** Not backtested yet  
**Decision:** Add only if backtest shows PF > 1.5

### Paper Trading

**Plan:** Run strategies on demo account for 30 days  
**Purpose:** Validate live performance vs backtest  
**Decision:** Implement after deployment
