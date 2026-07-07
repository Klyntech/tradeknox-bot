# 12 — Troubleshooting

## Common Issues

### Bot Won't Start

**Symptoms:** Bot crashes on startup

**Possible Causes:**
1. Missing TELEGRAM_TOKEN
2. Missing PRIVATE_CHANNEL_ID
3. Python version mismatch
4. Missing dependencies

**Solutions:**

```bash
# Check env vars
echo $TELEGRAM_TOKEN
echo $PRIVATE_CHANNEL_ID

# Check Python version
python --version  # Should be 3.11+

# Install dependencies
pip install -r requirements.txt

# Check logs
python app.py  # Look for error messages
```

---

### Bot Starts But No Signals

**Symptoms:** Bot runs but never sends signals

**Possible Causes:**
1. Market is closed (weekend/night)
2. Wrong session (Asia/Dead Zone)
3. Score too low (below 11/20)
4. Data source not working

**Solutions:**

```bash
# Check if market is open
# London: 07:00-12:00 UTC
# New York: 12:00-21:00 UTC

# Check logs for scan activity
grep "Scanning" logs/bot.log

# Check score threshold
# Default: 11/20 minimum

# Test data source
python -c "import yfinance as yf; print(yf.download('GC=F', period='5d'))"
```

---

### Telegram Bot Not Responding

**Symptoms:** Bot doesn't reply to /start

**Possible Causes:**
1. Wrong TELEGRAM_TOKEN
2. Bot not started in BotFather
3. Network issues
4. Bot blocked by user

**Solutions:**

```bash
# Verify token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Check bot status
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo

# Restart bot
python app.py
```

---

### Signals Not Appearing in Channel

**Symptoms:** Bot logs signals but channel is empty

**Possible Causes:**
1. Wrong PRIVATE_CHANNEL_ID
2. Bot not admin in channel
3. Channel is private

**Solutions:**

```bash
# Get channel ID
# Forward a message from channel to @userinfobot

# Add bot as admin
# Channel Settings → Administrators → Add Bot

# Verify channel ID
echo $PRIVATE_CHANNEL_ID
```

---

### Stripe Webhook Not Working

**Symptoms:** Payments not activating subscriptions

**Possible Causes:**
1. Wrong STRIPE_WEBHOOK_SECRET
2. Webhook URL not set in Stripe
3. Signature verification failing

**Solutions:**

```bash
# Check webhook secret
echo $STRIPE_WEBHOOK_SECRET

# Verify webhook URL in Stripe Dashboard
# Developers → Webhooks → Add endpoint
# URL: https://your-app.onrender.com/webhook

# Test webhook
curl -X POST https://your-app.onrender.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"type": "test"}'
```

---

### Render Free Tier Sleeping

**Symptoms:** Bot stops responding after 15 minutes

**Possible Causes:**
1. No UptimeRobot ping
2. Health endpoint not working

**Solutions:**

```bash
# Set up UptimeRobot
# 1. Go to uptimerobot.com
# 2. Add new monitor
# 3. URL: https://your-app.onrender.com/health
# 4. Interval: 5 minutes

# Test health endpoint
curl https://your-app.onrender.com/health
```

---

### Data Download Fails

**Symptoms:** scripts/download_data.py errors

**Possible Causes:**
1. Network issues
2. yfinance rate limited
3. Wrong ticker symbol

**Solutions:**

```bash
# Test yfinance
python -c "import yfinance as yf; print(yf.download('GC=F', period='5d'))"

# Check network
ping google.com

# Use different ticker
# XAUUSD: GC=F
# GBPJPY: GBPJPY=X
```

---

### Backtest Results Seem Wrong

**Symptoms:** Unusually high/low returns

**Possible Causes:**
1. Wrong data period
2. Look-ahead bias
3. Survivorship bias
4. Transaction costs not included

**Solutions:**

```bash
# Check data period
ls data/yfinance/
# Should have 800-900 rows (3.5 years)

# Verify no look-ahead
# Backtest uses only past data

# Include transaction costs
# Backtest includes 0.1% spread + 0.05% commission
```

---

### License Key Validation Fails

**Symptoms:** Users can't access signals

**Possible Causes:**
1. Wrong LICENSE_SECRET
2. Key expired
3. Key tampered

**Solutions:**

```bash
# Check LICENSE_SECRET
echo $LICENSE_SECRET

# Regenerate secret
python -c "import secrets; print(secrets.token_hex(32))"

# Update in Render dashboard
# Environment → LICENSE_SECRET
```

---

## Error Messages

### "TELEGRAM_TOKEN is not set"

**Cause:** Missing bot token  
**Fix:** Set TELEGRAM_TOKEN environment variable

### "PRIVATE_CHANNEL_ID is not set"

**Cause:** Missing channel ID  
**Fix:** Set PRIVATE_CHANNEL_ID environment variable

### "Max trades reached"

**Cause:** Daily limit hit (5 trades/day)  
**Fix:** Wait for next day or increase MAX_TRADES_PER_DAY

### "Session limit reached"

**Cause:** Session limit hit (3 trades/session)  
**Fix:** Wait for next session or increase MAX_TRADES_PER_SESSION

### "Score X/20 below threshold"

**Cause:** Signal quality too low  
**Fix:** This is normal — weak signals are filtered out

### "News blackout active"

**Cause:** High-impact news nearby  
**Fix:** Wait 30 minutes after news event

### "License key expired"

**Cause:** Subscription ended  
**Fix:** User needs to renew subscription

---

## Performance Issues

### Bot Running Slow

**Symptoms:** Scan takes > 10 seconds

**Causes:**
1. Slow data fetch
2. Too many pairs
3. Chart generation slow

**Fixes:**
- Reduce number of pairs
- Use faster data source
- Optimize chart generation

### Memory Usage High

**Symptoms:** Bot crashes with OOM

**Causes:**
1. Too much historical data
2. Memory leak
3. Large DataFrames

**Fixes:**
- Reduce data period
- Restart bot periodically
- Optimize DataFrame operations

---

## Getting Help

1. Check logs: `logs/bot.log`
2. Check health: `GET /health`
3. Check status: `/status` command
4. Check stats: `/stats` command
5. Contact support: @support

---

## Useful Commands

```bash
# Check bot status
curl https://your-app.onrender.com/health

# Check logs
# Render Dashboard → Logs

# Restart bot
# Render Dashboard → Manual Deploy

# Check Stripe webhooks
# Stripe Dashboard → Developers → Webhooks

# Test data source
python -c "import yfinance as yf; print(yf.download('GC=F', period='5d'))"
```
