# 13 — Changelog

All notable changes to TradeKnox.

---

## [0.3.0] — 2026-07-07

### Added
- 3 new backtested strategies from MarketMate:
  - EMA Crossover (MM-008): PF 2.17 on XAUUSD
  - Heikin Ashi Trend (MM-017): PF 1.67 on XAUUSD
  - Stochastic Extreme (MM-016): PF 1.69 on GBPJPY
- USDJPY as active pair (previously excluded)
- Multi-source data download:
  - `scripts/download_data.py` — yfinance + Dukascopy
  - `scripts/cross_validate.py` — data validation
  - `scripts/backtest_strategies.py` — strategy backtesting
- 3.5 years of historical data (Jan 2023 — Jul 2026)
- Comprehensive documentation:
  - `docs/README.md` — documentation hub
  - `docs/01-getting-started.md` — quick start guide
  - `docs/02-architecture.md` — system architecture
  - `docs/03-strategies.md` — all 8 strategies
  - `docs/04-scoring-system.md` — scoring breakdown
  - `docs/05-risk-management.md` — risk management
  - `docs/06-signal-pipeline.md` — 12-layer pipeline
  - `docs/07-deployment.md` — Render setup
  - `docs/08-revenue-model.md` — pricing and tiers
  - `docs/09-decisions.md` — all decisions
  - `docs/10-backtest-report.md` — full backtest results
  - `docs/11-api-reference.md` — commands and endpoints
  - `docs/12-troubleshooting.md` — common issues
  - `docs/13-changelog.md` — this file

### Changed
- Updated `PAIR_STRATEGIES` with new strategy weights
- Updated `strategies.py` with 3 new strategy functions
- Updated `.gitignore` to exclude data folder
- Updated `PROJECT.md` with new strategy info

### Fixed
- USDJPY now profitable with new strategies

---

## [0.2.0] — 2026-07-06

### Added
- Chart generation with OB/FVG/BOS overlays
- Blurred chart preview for free tier
- Reliability fixes:
  - Config validation (`validate()` and `validate_or_exit()`)
  - Retry logic for Telegram sends (3x with exponential backoff)
  - Graceful shutdown (SIGTERM/SIGINT handlers)
  - Health endpoint (`GET /health`)
  - Webhook security (reject when STRIPE_WEBHOOK_SECRET unset)
  - SQLite error handling (try/except on all DB operations)
- Unit tests (31 tests, 30 passing):
  - `tests/test_charts.py` — chart generation
  - `tests/test_entry_logic.py` — entry logic
  - `tests/test_scoring.py` — scoring engine
  - `tests/test_signal_output.py` — signal formatting
  - `tests/test_subscriptions.py` — license keys
- Landing page overhaul:
  - Particles background
  - Scroll progress bar
  - Typing animation
  - Count-up stats
  - FAQ section (23 questions)
  - Email capture
- SEO improvements:
  - `robots.txt`
  - `sitemap.xml`
  - Open Graph image
  - FAQ schema (JSON-LD)
  - Canonical URL
  - Analytics placeholder

### Changed
- Updated `App.tsx` with full rewrite
- Updated `index.css` with animations
- Updated `favicon.svg` with TradeKnox logo
- Updated `index.html` with meta tags

### Fixed
- Scan loop was dead code (never awaited)
- Subscribe callback was giving free upgrades
- Flask debug mode was True in production
- News filter was awarding free points
- LICENSE_SECRET was regenerating on restart

---

## [0.1.0] — 2026-07-05

### Added
- Initial project setup
- Brand selection: TradeKnox
- Base repo: trading_signal_bot
- GitHub repo: Klyntech/tradeknox-bot
- Full 12-layer signal pipeline:
  1. Session Filter
  2. News Blackout
  3. Max Trades Check
  4. Data Fetch (yfinance)
  5. Calculate Indicators (ATR, RSI, EMA, RVOL)
  6. Market Structure (Trend, BOS/CHoCH)
  7. Entry Logic (OB, FVG, Fibonacci)
  8. Strategy Confluence (MA, RSI, Breakout)
  9. Scoring (0-20 points)
  10. Risk Management (Position sizing, SL/TP)
  11. Trade Management (TP/SL alerts)
  12. Telegram Output (Formatted signals)
- Subscription system (HMAC license keys)
- Stripe webhook handler
- Telegram bot commands (/start, /subscribe, /status, /stats, /key, /help)
- Render deployment config
- Per-pair optimized strategies:
  - XAUUSD: MA 9/21, Breakout 10, RSI 30/70
  - GBPJPY: MA 50/200, Breakout 20, RSI 20/80
- Day-of-week filters
- Revenue model: Free/Pro/VIP + Course

### Decisions
- Brand: TradeKnox
- Base repo: trading_signal_bot
- Revenue model: Subscription + Course
- Payment processor: Stripe
- Hosting: Render Free Tier
- Data source: yfinance
- Subscription system: HMAC License Keys
- Anti-leak: Delayed Public Channel
- Symbols: XAUUSD + GBPJPY
- Strategy parameters: Per-pair optimization
- Score threshold: 11/20

---

## Version Numbering

- **Major (X.0.0):** Breaking changes, major features
- **Minor (0.X.0):** New features, non-breaking
- **Patch (0.0.X):** Bug fixes, small changes

## Release Dates

| Version | Date | Milestone |
|---------|------|-----------|
| 0.1.0 | 2026-07-05 | Initial release |
| 0.2.0 | 2026-07-06 | Reliability + Landing page |
| 0.3.0 | 2026-07-07 | New strategies + Documentation |

---

## Future Plans

### [0.4.0] — Deployment
- Telegram bot token
- Deploy to Render
- UptimeRobot keep-alive
- First live signals

### [0.5.0] — Monetization
- Payment processor (Paystack/Telegram Stars)
- Stripe integration (when 18+)
- License key activation
- Subscription management

### [0.6.0] — Growth
- Paper trading validation
- Walk-forward testing
- Monte Carlo simulation
- Additional pairs (AUDUSD, NZDUSD)

### [1.0.0] — Production
- Full production deployment
- 100+ active users
- Consistent profitability
- Course published on Gumroad
