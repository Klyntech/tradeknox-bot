# 07 — Deployment

## Overview

TradeKnox deploys to **Render Free Tier** as a single process running both Flask (webhooks) and Telegram (bot polling).

## Prerequisites

1. GitHub account
2. Render account (free)
3. Telegram bot token from @BotFather
4. Stripe account (for payments)

## Step 1: Push to GitHub

```bash
git add .
git commit -m "feat: initial deployment"
git push origin main
```

## Step 2: Connect to Render

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Select `tradeknox-bot`

## Step 3: Configure Service

| Setting | Value |
|---------|-------|
| Name | tradeknox-bot |
| Region | Oregon (or closest) |
| Branch | main |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python app.py` |
| Instance Type | Free |

## Step 4: Set Environment Variables

In Render dashboard → Environment tab:

### Required

```bash
TELEGRAM_TOKEN=your_bot_token_here
PRIVATE_CHANNEL_ID=-100XXXXXXXXX
LICENSE_SECRET=generate_with_python_script
```

### Stripe (for payments)

```bash
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_VIP=price_...
DOMAIN=https://tradeknox.onrender.com
```

### Optional

```bash
ACCOUNT_BALANCE=10000
NEWS_API_KEY=
PUBLIC_CHANNEL_ID=
DATA_SOURCE=yfinance
```

## Step 5: Deploy

1. Click "Create Web Service"
2. Render auto-detects `render.yaml`
3. Build starts (~2-3 minutes)
4. Bot starts on `https://tradeknox.onrender.com`

## Step 6: Verify

1. Check logs for "Bot started successfully"
2. Open Telegram, find your bot
3. Send `/start`
4. Send `/status` to verify

## render.yaml

```yaml
services:
  - type: web
    name: tradeknox-bot
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: TELEGRAM_TOKEN
        sync: false
      - key: PRIVATE_CHANNEL_ID
        sync: false
      - key: LICENSE_SECRET
        generateValue: true
      - key: STRIPE_SECRET_KEY
        sync: false
      - key: STRIPE_WEBHOOK_SECRET
        sync: false
      - key: DOMAIN
        value: https://tradeknox.onrender.com
```

## Procfile

```
web: python app.py
```

## Keep-Alive

Render Free Tier sleeps after 15 minutes of inactivity. Use UptimeRobot to ping the health endpoint:

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Add new monitor
3. URL: `https://tradeknox.onrender.com/health`
4. Interval: 5 minutes

## Health Endpoint

```python
@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "telegram": "configured" if CONFIG.TELEGRAM_TOKEN != "YOUR_BOT_TOKEN" else "missing",
        "stripe": "configured" if CONFIG.STRIPE_SECRET_KEY else "missing",
        "database": check_db_health(),
    }), 200
```

## Webhook Endpoint

Stripe sends webhooks to:

```
https://tradeknox.onrender.com/webhook
```

**Important:** Set this URL in Stripe Dashboard → Webhooks.

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| TELEGRAM_TOKEN | Yes | — | Bot token from @BotFather |
| PRIVATE_CHANNEL_ID | Yes | — | Channel ID for signals |
| LICENSE_SECRET | Yes | Auto-generated | HMAC key for license signing |
| STRIPE_SECRET_KEY | Yes* | — | Stripe API key |
| STRIPE_WEBHOOK_SECRET | Yes* | — | Stripe webhook secret |
| STRIPE_PRICE_PRO | Yes* | — | Stripe Price ID for Pro |
| STRIPE_PRICE_VIP | Yes* | — | Stripe Price ID for VIP |
| DOMAIN | Yes* | — | Your Render URL |
| ACCOUNT_BALANCE | No | 10000 | Account size for risk calc |
| NEWS_API_KEY | No | — | ForexFactory API key |
| PUBLIC_CHANNEL_ID | No | — | Public channel (delayed) |
| DATA_SOURCE | No | yfinance | Data provider |
| TRADES_DB_PATH | No | trades.db | Trades database |
| LICENSES_DB_PATH | No | licenses.db | Licenses database |

*Required for payments

## Troubleshooting

### Bot won't start

1. Check logs for errors
2. Verify TELEGRAM_TOKEN is set
3. Verify PRIVATE_CHANNEL_ID is set

### Bot starts but no signals

1. Check if market is open (London/NY sessions)
2. Check logs for scan loop activity
3. Verify data source is working

### Webhook not receiving

1. Verify STRIPE_WEBHOOK_SECRET is set
2. Check Stripe Dashboard → Webhooks
3. Verify URL is correct

### Bot sleeps

1. Set up UptimeRobot ping
2. Health endpoint: `/health`
3. Interval: 5 minutes

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set env vars
export TELEGRAM_TOKEN=your_token
export PRIVATE_CHANNEL_ID=your_channel_id

# Run
python app.py
```

## Updating

1. Push changes to GitHub
2. Render auto-deploys
3. Check logs for successful restart

## Scaling

When you outgrow Free Tier:

1. Upgrade to Starter ($7/month)
2. No more sleeping
3. Better performance
4. Custom domain support
