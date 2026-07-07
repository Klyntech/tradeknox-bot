# 01 — Getting Started

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Telegram bot token from @BotFather
- A Telegram channel (private) for signal delivery

## 1. Clone the Repo

```bash
git clone https://github.com/Klyntech/tradeknox-bot.git
cd tradeknox-bot
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- python-telegram-bot (Telegram API)
- Flask (webhook server)
- yfinance (market data)
- pandas, numpy (data processing)
- matplotlib, Pillow (chart generation)
- requests (HTTP client)

## 3. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Required
TELEGRAM_TOKEN=your_bot_token_here
PRIVATE_CHANNEL_ID=-100XXXXXXXXX
LICENSE_SECRET=your_random_secret_here

# Stripe (optional for now)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_PRO=
STRIPE_PRICE_VIP=
DOMAIN=https://your-app.onrender.com

# Optional
ACCOUNT_BALANCE=10000
NEWS_API_KEY=
PUBLIC_CHANNEL_ID=
```

### Generating a LICENSE_SECRET

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 4. Run Locally

```bash
python app.py
```

The bot will:
1. Validate configuration
2. Start Flask webhook server on port 5000
3. Start Telegram bot polling
4. Begin scanning for signals every 5 minutes

## 5. Test the Bot

1. Open Telegram
2. Find your bot (by username)
3. Send `/start`
4. You should see a welcome message
5. Send `/status` to see bot status
6. Send `/help` to see all commands

## 6. First Signal

The bot scans automatically every 5 minutes during market hours (London/NY sessions). When a signal is found:

1. Bot scores the signal (must pass 11/20 threshold)
2. Bot renders a chart with entry/SL/TP levels
3. Bot sends formatted signal to your private channel
4. Free users see delayed signals (15 min), Pro/VIP see instantly

## Project Structure

```
tradeknox-bot/
├── app.py                 # Entry point (Flask + Telegram)
├── bot.py                 # Main bot logic, scan loop
├── strategies.py          # 8 backtested strategies
├── scoring_engine.py      # Signal scoring (0-20 points)
├── data_layer.py          # Price feeds, indicators
├── market_structure.py    # Trend, BOS/CHoCH, liquidity
├── entry_logic.py         # Order blocks, FVGs, Fibonacci
├── signal_output.py       # Telegram formatting
├── charts.py              # Chart generation
├── commands.py            # Bot commands (/start, /subscribe)
├── stripe_webhook.py      # Stripe webhook handling
├── subscriptions.py       # License key system
├── user_manager.py        # User registration, tier gating
├── config.py              # All environment variables
├── requirements.txt       # Python dependencies
├── render.yaml            # Render deployment config
├── Procfile               # Process definition
├── tests/                 # Unit tests (31 tests)
├── scripts/               # Data download, backtest tools
├── data/                  # Historical data (yfinance, dukascopy)
├── frontend/              # Landing page (React + Tailwind)
└── docs/                  # This documentation
```

## Next Steps

- [Architecture](02-architecture.md) — Understand the system
- [Strategies](03-strategies.md) — See what strategies are used
- [Deployment](07-deployment.md) — Deploy to Render
