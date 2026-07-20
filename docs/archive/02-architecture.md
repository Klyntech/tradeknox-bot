# 02 — Architecture

## System Overview

TradeKnox is a single-process application that runs both a Flask webhook server and a Telegram bot polling loop. It scans forex pairs for trading signals, scores them against a weighted system, and sends formatted signals to a Telegram channel.

```
┌─────────────────────────────────────────────────────────────┐
│                        app.py                               │
│                    (Entry Point)                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Flask Server     │    │  Telegram Bot     │              │
│  │  (Webhooks)       │    │  (Polling)        │              │
│  │  Port 5000        │    │  Main Thread      │              │
│  └────────┬─────────┘    └────────┬─────────┘              │
│           │                       │                         │
│           ▼                       ▼                         │
│  ┌──────────────────────────────────────────┐              │
│  │              bot.py                       │              │
│  │         (Orchestrator)                    │              │
│  │    Scan Loop → Signal Pipeline → Output   │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
tradeknox-bot/
│
├── app.py                    # Entry point — starts Flask + Telegram
│
├── bot.py                    # Orchestrator — scan loop, signal pipeline
│
├── data_layer.py             # Price feeds, indicator calculations
│   ├── fetch_ohlcv()         # Get candle data from yfinance
│   ├── calculate_indicators() # ATR, RSI, EMA, RVOL
│   └── DataFeed class        # Multi-timeframe data management
│
├── market_structure.py       # Market structure analysis
│   ├── classify_trend()      # BULLISH / BEARISH / FLAT
│   ├── detect_bos()          # Break of Structure
│   ├── detect_choch()        # Change of Character
│   ├── detect_liquidity()    # Liquidity zones
│   └── Structure dataclass   # Trend, BOS, CHoCH, zones
│
├── entry_logic.py            # Entry zone detection
│   ├── detect_order_blocks() # Order blocks (OB)
│   ├── detect_fvg()          # Fair Value Gaps (FVG)
│   ├── detect_fib()          # Fibonacci levels
│   ├── detect_candle()       # Candlestick patterns
│   └── EntrySetup dataclass  # Complete entry analysis
│
├── strategies.py             # 8 backtested strategies
│   ├── detect_ma_crossover() # MA 9/21, 50/200
│   ├── detect_breakout()     # N-bar breakout
│   ├── detect_rsi_extremes() # RSI 20/80 reversal
│   ├── detect_ema_crossover() # EMA crossover (MM-008)
│   ├── detect_heikin_ashi_trend() # Heikin Ashi (MM-017)
│   ├── detect_stochastic_extreme() # Stochastic (MM-016)
│   ├── detect_session_entry() # Session timing
│   ├── detect_ema_alignment() # EMA alignment
│   └── PAIR_STRATEGIES dict  # Per-pair configs
│
├── scoring_engine.py         # Signal scoring (0-20 points)
│   ├── score_signal()        # Main scoring function
│   ├── assess_indicators()   # Indicator confluence
│   ├── build_risk_profile()  # Position sizing
│   └── SignalScore dataclass # Score breakdown
│
├── signal_output.py          # Telegram signal formatting
│   ├── format_signal_message() # Build signal text
│   ├── format_price()        # Price formatting per pair
│   └── send_signal()         # Send to Telegram channel
│
├── charts.py                 # Chart generation
│   ├── render_signal_chart() # Candlestick + indicators
│   ├── render_blurred_chart() # Free tier preview
│   └── draw_order_blocks()   # OB/FVG overlays
│
├── commands.py               # Bot command handlers
│   ├── /start                # Welcome message
│   ├── /subscribe            # Payment link
│   ├── /status               # Bot status
│   ├── /stats                # Performance stats
│   ├── /key                  # License key management
│   └── /help                 # Command list
│
├── stripe_webhook.py         # Stripe integration
│   ├── create_checkout()     # Start payment
│   ├── handle_webhook()      # Process events
│   └── WebhookEvent enum     # checkout.completed, etc.
│
├── subscriptions.py          # License key system
│   ├── generate_key()        # HMAC license generation
│   ├── validate_key()        # Key validation
│   └── LicenseKey dataclass  # Key structure
│
├── user_manager.py           # User management
│   ├── register_user()       # New user registration
│   ├── check_tier()          # Get user tier
│   ├── can_receive_signal()  # Tier + limit check
│   └── User dataclass        # User structure
│
├── config.py                 # Configuration
│   ├── BotConfig dataclass   # All env vars + defaults
│   ├── validate()            # Config validation
│   └── CONFIG singleton      # Global config instance
│
├── requirements.txt          # Python dependencies
├── render.yaml               # Render deployment
├── Procfile                  # Process definition
│
├── tests/                    # Unit tests
│   ├── test_charts.py        # Chart generation tests
│   ├── test_entry_logic.py   # Entry logic tests
│   ├── test_scoring.py       # Scoring engine tests
│   ├── test_signal_output.py # Signal formatting tests
│   └── test_subscriptions.py # License key tests
│
├── scripts/                  # Utility scripts
│   ├── download_data.py      # Download historical data
│   ├── cross_validate.py     # Validate data across sources
│   └── backtest_strategies.py # Backtest strategies
│
├── data/                     # Historical data
│   ├── yfinance/             # Daily data from yfinance
│   └── dukascopy/            # Hourly data from Dukascopy
│
├── frontend/                 # Landing page
│   ├── src/                  # React components
│   ├── index.html            # Entry point
│   └── package.json          # Dependencies
│
└── docs/                     # This documentation
```

## Data Flow

### Signal Generation Flow

```
1. Scan Loop (every 5 min)
   └── For each pair (XAUUSD, GBPJPY, USDJPY)
       │
       ├── 2. Session Filter
       │   └── Is it London/NY/Overlap? → Skip if not
       │
       ├── 3. News Blackout
       │   └── High-impact news within 30min? → Skip if yes
       │
       ├── 4. Max Trades Check
       │   └── Already hit daily limit? → Skip if yes
       │
       ├── 5. Data Fetch
       │   └── Get OHLCV from yfinance (15m, 1h, 4h)
       │
       ├── 6. Calculate Indicators
       │   └── ATR, RSI, EMA, RVOL
       │
       ├── 7. Market Structure
       │   └── Trend, BOS/CHoCH, liquidity zones
       │
       ├── 8. Entry Logic
       │   └── Order blocks, FVGs, Fibonacci, candle patterns
       │
       ├── 9. Strategy Confluence
       │   └── Run 8 strategies, check alignment
       │
       ├── 10. Scoring
       │   └── Score 0-20, check threshold (11/20)
       │
       ├── 11. Risk Management
       │   └── Position size, SL/TP, R:R validation
       │
       └── 12. Output
           └── Format signal, render chart, send to Telegram
```

### Webhook Flow

```
1. Stripe sends webhook to /webhook
   │
   ├── 2. Verify signature
   │   └── Reject if invalid
   │
   ├── 3. Parse event type
   │   ├── checkout.session.completed → Activate subscription
   │   ├── customer.subscription.updated → Handle renewal
   │   ├── customer.subscription.deleted → Deactivate
   │   └── invoice.payment_failed → Handle failure
   │
   └── 4. Update database
       └── Write to licenses.db
```

## Dependencies

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| python-telegram-bot | 20+ | Telegram API |
| Flask | 3.0+ | Webhook server |
| yfinance | 0.2+ | Market data |
| pandas | 2.0+ | Data processing |
| numpy | 1.24+ | Numerical computing |
| matplotlib | 3.7+ | Chart generation |
| Pillow | 10.0+ | Image processing |
| requests | 2.31+ | HTTP client |

### External Services

| Service | Purpose | Required? |
|---------|---------|-----------|
| Telegram Bot API | Signal delivery | Yes |
| yfinance | Market data | Yes (default) |
| Stripe | Payments | Yes (for monetization) |
| Render | Hosting | Yes (for deployment) |
| ForexFactory API | News filter | Optional |

## Module Responsibilities

### app.py (Entry Point)
- Initializes Flask and Telegram
- Starts the scan loop in a background thread
- Handles graceful shutdown

### bot.py (Orchestrator)
- Manages the scan loop (every 5 minutes)
- Calls each layer of the signal pipeline
- Coordinates between modules

### data_layer.py (Data)
- Fetches OHLCV data from yfinance
- Calculates technical indicators
- Manages multi-timeframe data

### market_structure.py (Structure)
- Classifies market trend (BULLISH/BEARISH/FLAT)
- Detects Break of Structure (BOS)
- Detects Change of Character (CHoCH)
- Identifies liquidity zones

### entry_logic.py (Entry)
- Detects Order Blocks (OB)
- Detects Fair Value Gaps (FVG)
- Calculates Fibonacci levels
- Identifies candlestick patterns

### strategies.py (Strategies)
- Implements 8 backtested strategies
- Manages per-pair configurations
- Calculates strategy confluence

### scoring_engine.py (Scoring)
- Scores signals across 6 categories
- Applies threshold gate (11/20 minimum)
- Calculates position sizing

### signal_output.py (Output)
- Formats Telegram messages
- Manages price formatting
- Handles signal delivery

### charts.py (Charts)
- Renders candlestick charts
- Adds indicators and overlays
- Generates blurred preview for free tier

### commands.py (Commands)
- Handles bot commands (/start, /subscribe, etc.)
- Manages user interactions
- Provides bot status and stats

### stripe_webhook.py (Payments)
- Handles Stripe webhook events
- Manages subscription lifecycle
- Processes payments

### subscriptions.py (License)
- Generates HMAC license keys
- Validates keys on each scan
- Manages subscription status

### user_manager.py (Users)
- Registers new users
- Checks tier access
- Enforces signal limits

### config.py (Configuration)
- Loads environment variables
- Validates configuration
- Provides defaults
