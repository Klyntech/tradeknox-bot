# Tasks

## Completed

### Phase 1: Setup
- [x] Audit all repos across Klyntech and noventra-io
- [x] Select brand name: TradeKnox
- [x] Identify base repo: trading_signal_bot
- [x] Install and authenticate GitHub CLI
- [x] Design revenue model (Free/Pro/VIP + Course) — ABANDONED, bot is free
- [x] Draft full execution plan
- [x] Create GitHub repo Klyntech/tradeknox-bot
- [x] Copy base code into new repo
- [x] Create PROJECT.md, TASKS.md, DECISIONS.md

### Phase 2: Core Bot
- [x] Build full 12-layer signal pipeline
- [x] Add subscription/license system (subscriptions.py, user_manager.py)
- [x] Add Stripe webhook handler (stripe_webhook.py)
- [x] Add Telegram bot commands (/start, /subscribe, /status, /stats, /key, /help)
- [x] Add Render deployment config (render.yaml, Procfile)

### Phase 3: Research — Old (Indicator Strategies)
- [x] Download 6 months of historical data (5 symbols, 4 timeframes)
- [x] Run market profile analysis
- [x] Test 17 strategies across all symbols and timeframes
- [x] Find optimal strategy combinations
- [x] Optimize per-pair parameters
- [x] Add day-of-week filters

### Phase 4: Research — SMC 8-Gate
- [x] Build SMC 8-Gate pipeline (market_structure.py, entry_logic.py, scoring_engine.py)
- [x] Delete all 8 indicator-based strategies (MarketMate Graveyard)
- [x] Download 20+ years of data for 8 pairs (32 CSV files)
- [x] Build fast_backtest.py and pipeline_backtest.py
- [x] Validate SMC 8-Gate (PF 3.65 on XAUUSD)

### Phase 5: Deployment
- [x] Fix scan loop (was dead code, never awaited)
- [x] Fix subscribe callback (was giving free upgrades)
- [x] Combine Flask + Telegram into single process for Render free tier
- [x] Deploy to Render
- [x] Fix LICENSE_SECRET regeneration on restart
- [x] Add health endpoint

### Phase 6: Strategy Discovery (Brainstorm Batch)
- [x] Test 5 fresh strategies (Jul 10, 2026)
- [x] Discover False Breakout Trap (PF 2.39 on GBPUSD)
- [x] Run full adversarial validation on False Breakout
- [x] Result: 6/6 on all 5 pairs — production ready
- [x] Reject 9EMA+RSI, BB Walk, Vol Disconnect, V-Shape
- [x] Reject MM-012 Gap Fill (failed adversarial)
- [x] Re-classify MM-002 as marginal (5/6 tests)
- [x] Update all docs with current strategy state

## Next

- [ ] Integrate False Breakout into bot.py as secondary scanner
- [ ] Test dual-strategy (SMC + False Breakout) portfolio performance
- [ ] Add regime-based strategy selection (SMC for trending, False Breakout for ranging)
- [ ] Create public channel @TradeKnoxSignals
- [ ] Write "SMC Trading Blueprint" PDF course
