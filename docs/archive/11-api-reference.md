# 11 — API Reference

## Bot Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/start` | Welcome message, register user | All |
| `/subscribe` | Show subscription options | All |
| `/status` | Bot status and uptime | All |
| `/stats` | Performance statistics | All |
| `/key` | Manage license key | All |
| `/help` | List all commands | All |
| `/cancel` | Cancel current operation | All |

---

### /start

**Description:** Welcome message and user registration

**Response:**
```
Welcome to TradeKnox! 🏛️

I scan XAUUSD, GBPJPY, and USDJPY for high-probability trading setups using Smart Money Concepts.

📊 What I Provide:
• Entry, Stop Loss, Take Profit levels
• Risk management details
• Professional charts with OB/FVG overlays

🆓 Free Tier: 3 signals/day (15 min delay)
💎 Pro: $29/mo — Unlimited, instant
👑 VIP: $49/mo — + Risk mgmt + Course

Type /subscribe to get started!
```

**Side effects:**
- Registers user in database
- Sets tier to "free"

---

### /subscribe

**Description:** Show subscription options

**Response:**
```
Choose your plan:

🆓 Free — $0
• 3 signals/day
• 15 minute delay
• Blurred charts

💎 Pro — $29/mo
• Unlimited signals
• Instant delivery
• Full charts
• [Subscribe to Pro]

👑 VIP — $49/mo
• Everything in Pro
• Risk management
• SMC Trading Blueprint course
• [Subscribe to VIP]
```

**Inline buttons:**
- "Subscribe to Pro" → Stripe Checkout
- "Subscribe to VIP" → Stripe Checkout

---

### /status

**Description:** Bot status and uptime

**Response:**
```
📊 TradeKnox Status

⏱️ Uptime: 2d 5h 32m
📡 Status: Active
🔍 Scanning: XAUUSD, GBPJPY, USDJPY
⏰ Scan Interval: 5 minutes
📅 Last Scan: 2026-07-07 12:45 UTC

🎯 Today's Signals: 4
✅ Active Users: 23
```

---

### /stats

**Description:** Performance statistics

**Response:**
```
📈 TradeKnox Performance

📅 Period: Last 30 days
📊 Total Signals: 87
✅ Win Rate: 54.2%
💰 Avg R:R: 1.52:1
📈 Profit Factor: 1.68

🏆 Best Pair: XAUUSD (PF 2.17)
📊 Total Trades: 234
💰 Avg Return: +1.2% per trade
```

---

### /key

**Description:** Manage license key

**Response (Free user):**
```
🔑 Your License Key

Tier: Free
Key: TK-FREE-XXXX-XXXX
Expires: Never

Upgrade for more features:
/subscribe
```

**Response (Pro user):**
```
🔑 Your License Key

Tier: Pro
Key: TK-PRO-XXXX-XXXX
Expires: 2026-08-07
Status: Active

Manage: /key
```

---

### /help

**Description:** List all commands

**Response:**
```
📚 TradeKnox Commands

/start — Welcome message
/subscribe — Get Pro or VIP
/status — Bot status
/stats — Performance stats
/key — Manage license key
/help — This message

💬 Questions? Contact @support
```

---

## Webhook Endpoints

### POST /webhook

**Description:** Stripe webhook handler

**Headers:**
```
Content-Type: application/json
Stripe-Signature: whsec_...
```

**Body:** Stripe event object

**Events Handled:**

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Activate subscription |
| `customer.subscription.updated` | Handle renewal |
| `customer.subscription.deleted` | Deactivate |
| `invoice.payment_failed` | Handle failure |

**Response:**
```json
{"received": true}
```

**Security:**
- Verifies Stripe signature
- Rejects if STRIPE_WEBHOOK_SECRET not set
- Logs all events

---

### GET /health

**Description:** Health check endpoint

**Response (200):**
```json
{
  "status": "healthy",
  "telegram": "configured",
  "stripe": "configured",
  "database": "ok"
}
```

**Response (503):**
```json
{
  "status": "unhealthy",
  "telegram": "missing",
  "stripe": "missing",
  "database": "error"
}
```

---

### GET /

**Description:** Landing page

**Response:** HTML page (React app)

---

## Configuration Options

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TELEGRAM_TOKEN` | string | — | Bot token from @BotFather |
| `PRIVATE_CHANNEL_ID` | string | — | Channel ID for signals |
| `PUBLIC_CHANNEL_ID` | string | "" | Public channel (delayed) |
| `LICENSE_SECRET` | string | — | HMAC key for license signing |
| `STRIPE_SECRET_KEY` | string | — | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | string | — | Stripe webhook secret |
| `STRIPE_PRICE_PRO` | string | — | Stripe Price ID for Pro |
| `STRIPE_PRICE_VIP` | string | — | Stripe Price ID for VIP |
| `DOMAIN` | string | — | Your Render URL |
| `ACCOUNT_BALANCE` | float | 10000 | Account size for risk calc |
| `DEFAULT_RISK_PCT` | float | 1.0 | Risk per trade (%) |
| `MIN_SCORE_THRESHOLD` | int | 11 | Minimum score (0-20) |
| `MIN_CONFIDENCE_PCT` | float | 55.0 | Minimum confidence (%) |
| `SCAN_INTERVAL_SECONDS` | int | 300 | Scan interval (seconds) |
| `DATA_SOURCE` | string | yfinance | Data provider |
| `NEWS_API_KEY` | string | "" | ForexFactory API key |
| `TRADES_DB_PATH` | string | trades.db | Trades database |
| `LICENSES_DB_PATH` | string | licenses.db | Licenses database |

---

## Database Schema

### trades.db

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    pair TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    stop_loss REAL,
    tp1 REAL,
    tp2 REAL,
    tp3 REAL,
    score INTEGER,
    confidence REAL,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);
```

### licenses.db

```sql
CREATE TABLE licenses (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tier TEXT NOT NULL,
    key TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    tier TEXT DEFAULT 'free',
    signals_today INTEGER DEFAULT 0,
    last_signal_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Error Codes

| Code | Description | Action |
|------|-------------|--------|
| 400 | Bad request | Check request format |
| 401 | Unauthorized | Check API key |
| 403 | Forbidden | Check permissions |
| 404 | Not found | Check endpoint |
| 500 | Server error | Check logs |
| 503 | Service unavailable | Bot may be starting |

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| /webhook | 100 req/min | Per IP |
| /health | 1000 req/min | Per IP |
| Telegram API | 30 msg/sec | Global |

---

## Code Reference

Commands: `commands.py`  
Webhook: `stripe_webhook.py`  
Config: `config.py`  
Database: `data_layer.py`
