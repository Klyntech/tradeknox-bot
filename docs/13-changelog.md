# 13 — Changelog

All notable changes to TradeKnox.

---

## [0.4.0] — 2026-07-10

### Added
- **False Breakout Trap** — new counter-trend strategy discovered via brainstorming
  - PF 2.39 on GBPUSD, PF 2.34 on EURUSD
  - Passed 6/6 adversarial tests on ALL 5 validated pairs
  - 0.0% probability PF < 1.0 (bootstrap, all pairs)
  - Works in ALL regimes: PF 2.77 in RANGING, PF 2.03 in TRENDING
- Full adversarial validation framework in `research/`:
  - `gap_backtest.py` — MM-002/MM-012 grid sweep + 6 adversarial tests
  - `adversarial_false_breakout.py` — 6-test suite for False Breakout
  - `brainstorm_test.py` — 5 fresh strategy tests (1 winner)
- Strategy differentiation: SMC 8-Gate (trend) + False Breakout (reversal)
- All docs updated to reflect deleted indicator strategies

### Changed
- **docs/03-strategies.md** — Rewritten: 2 validated strategies, SMC 8-Gate + False Breakout
- **docs/10-backtest-report.md** — Rewritten: adversarial results, graveyard, test methodology
- **PROJECT.md** — Updated pairs (8), strategies (2), current status
- **DECISIONS.md** — Added False Breakout decision, regime-based deployment
- **TASKS.md** — Updated completed/blocked/next

### Removed
- All 8 indicator-based strategies from documentation (MarketMate Graveyard):
  - MA Crossover, Breakout, RSI Extremes, EMA Crossover (MM-008)
  - Heikin Ashi Trend (MM-017), Stochastic Extreme (MM-016)
  - Session Timing, EMA Alignment
- MM-019 through MM-025 from strategy list (were deleted from code in v0.3.x)

### Fixed
- Documentation no longer references deleted strategies or outdated pairs

---

## [0.3.0] — 2026-07-07

### Added
- 3 new backtested strategies from MarketMate:
  - EMA Crossover (MM-008): PF 2.17 on XAUUSD
  - Heikin Ashi Trend (MM-017): PF 1.67 on XAUUSD
  - Stochastic Extreme (MM-016): PF 1.69 on GBPJPY
- USDJPY as active pair (previously excluded)
- Multi-source data download
- 3.5 years of historical data (Jan 2023 — Jul 2026)
- Comprehensive documentation set (13 docs)

### Changed
- Updated `PAIR_STRATEGIES` with new strategy weights
- Updated `strategies.py` with 3 new strategy functions

### Fixed
- USDJPY now profitable with new strategies

---

## [0.2.0] — 2026-07-06

### Added
- Chart generation with OB/FVG/BOS overlays
- Blurred chart preview for free tier
- Reliability fixes (retry logic, graceful shutdown, health endpoint)
- Unit tests (31 tests, 30 passing)
- Landing page overhaul (particles, animations, FAQ)
- SEO improvements

### Changed
- Full rewrite of `App.tsx` and `index.css`

### Fixed
- Scan loop dead code (never awaited)
- Subscribe callback free upgrades
- Flask debug mode in production
- News filter free points

---

## [0.1.0] — 2026-07-05

### Added
- Initial project setup
- Brand: TradeKnox
- Full 12-layer signal pipeline
- Subscription system (HMAC license keys)
- Stripe webhook handler
- Telegram bot commands
- Render deployment config
- Per-pair optimized strategies (XAUUSD, GBPJPY)

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
| 0.4.0 | 2026-07-10 | False Breakout + Adversarial validation |
