# Tasks

## Completed

### Phase 1: Setup
- [x] Audit all repos across Klyntech and noventra-io
- [x] Select brand name: TradeKnox
- [x] Identify base repo: trading_signal_bot
- [x] Install and authenticate GitHub CLI
- [x] Design revenue model (Free/Pro/VIP + Course)
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

### Phase 3: Research
- [x] Download 6 months of historical data (5 symbols, 4 timeframes)
- [x] Run market profile analysis
- [x] Test 17 strategies across all symbols and timeframes
- [x] Find optimal strategy combinations
- [x] Optimize per-pair parameters
- [x] Add day-of-week filters

### Phase 4: Deployment Fixes
- [x] Fix scan loop (was dead code, never awaited)
- [x] Fix subscribe callback (was giving free upgrades)
- [x] Implement 4 Stripe webhook TODOs (key delivery, renewal, failure, cancellation)
- [x] Combine Flask + Telegram into single process for Render free tier

### Phase 5: Code Quality
- [x] Fix LICENSE_SECRET regeneration on restart
- [x] Fix Flask debug mode (was True in production)
- [x] Fix news filter scoring (was awarding free points)
- [x] Update landing page stats to match backtest data
- [x] Centralize DB paths via env vars
- [x] Remove 12 unused imports
- [x] Create root README.md
- [x] Update stale docs (PROJECT.md, TASKS.md, DECISIONS.md)

## Blocked

- [ ] Telegram bot token from @BotFather (phone unavailable)
- [ ] Stripe account + API keys + Price IDs
- [ ] Deploy to Render (needs above credentials)

## Next

- [ ] Test bot locally with Telegram
- [ ] Deploy to Render
- [ ] Create public channel @TradeKnoxSignals
- [ ] Launch publicly, post first signals
- [ ] Write "SMC Trading Blueprint" PDF course
- [ ] Publish course on Gumroad ($39)
- [ ] Add UptimeRobot keep-alive ping
