# 08 — Revenue Model

## Overview

TradeKnox uses a **freemium subscription model** with three tiers plus a one-time course purchase.

## Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 3 signals/day, 15 min delay, blurred charts |
| **Pro** | $29/mo | Unlimited signals, instant delivery, full charts |
| **VIP** | $49/mo | Everything in Pro + risk management + course |
| **Course** | $39 one-time | "SMC Trading Blueprint" PDF on Gumroad |

## Free Tier

**Purpose:** Acquisition funnel — let users experience value before paying.

**Limits:**
- 3 signals per day
- 15-minute delay (Pro/VIP get instantly)
- Blurred chart preview
- No risk management details

**Why limits work:**
- Users see signals are valuable
- Delay creates urgency
- Blurred charts tease the full experience

## Pro Tier ($29/mo)

**Target:** Active traders who want real-time signals.

**Features:**
- Unlimited signals
- Instant delivery (no delay)
- Full charts with OB/FVG/BOS overlays
- Entry, SL, TP levels
- Position sizing details

**Value proposition:** "Get the same signals as VIP without the course."

## VIP Tier ($49/mo)

**Target:** Serious traders who want education + signals.

**Features:**
- Everything in Pro
- Risk management breakdown
- "SMC Trading Blueprint" course included
- Priority support (future)

**Value proposition:** "Signals + education in one package."

## Course ($39 one-time)

**Title:** "SMC Trading Blueprint"

**Format:** PDF on Gumroad

**Contents:**
- Smart Money Concepts explained
- Order blocks, FVGs, liquidity
- Entry/exit strategies
- Risk management rules
- Trade journal template

**Purpose:** Standalone product + VIP bonus.

## Payment Flow

### Stripe Checkout

```
1. User sends /subscribe to bot
2. Bot sends inline keyboard with tier options
3. User clicks tier → Bot creates Stripe Checkout session
4. User redirected to Stripe Checkout
5. User enters card details
6. Stripe processes payment
7. Stripe sends webhook to /webhook
8. Bot activates subscription
9. Bot sends license key to user
```

### License Key System

```python
@dataclass
class LicenseKey:
    key: str           # HMAC-signed key
    user_id: int       # Telegram user ID
    tier: str          # "free", "pro", "vip"
    expires_at: datetime  # Subscription end date
    created_at: datetime
```

**Validation:** Bot validates license key on each scan cycle.

### Webhook Events

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Activate subscription |
| `customer.subscription.updated` | Handle renewal |
| `customer.subscription.deleted` | Deactivate |
| `invoice.payment_failed` | Handle failure |

## Revenue Projections

### Conservative (100 users)

| Tier | Users | Monthly Revenue |
|------|-------|-----------------|
| Free | 70 | $0 |
| Pro | 20 | $580 |
| VIP | 10 | $490 |
| **Total** | 100 | **$1,070/mo** |

### Moderate (500 users)

| Tier | Users | Monthly Revenue |
|------|-------|-----------------|
| Free | 350 | $0 |
| Pro | 100 | $2,900 |
| VIP | 50 | $2,450 |
| **Total** | 500 | **$5,350/mo** |

### Aggressive (2000 users)

| Tier | Users | Monthly Revenue |
|------|-------|-----------------|
| Free | 1400 | $0 |
| Pro | 400 | $11,600 |
| VIP | 200 | $9,800 |
| **Total** | 2000 | **$21,400/mo** |

## Costs

| Cost | Monthly | Notes |
|------|---------|-------|
| Render | $0 | Free tier |
| yfinance | $0 | Free data |
| Stripe | ~3% | Transaction fees |
| Domain | ~$1 | If purchased |
| **Total** | **~$1-100** | Scales with revenue |

## Marketing Strategy

### Phase 1: Launch (Week 1-2)

1. Create Telegram channel @TradeKnoxSignals
2. Post 5-10 free signals daily
3. Share in trading communities
4. Get 10-20 free users

### Phase 2: Growth (Week 3-4)

1. Show performance stats
2. Offer Pro/VIP trials
3. Collect testimonials
4. Target 50-100 free users

### Phase 3: Monetize (Month 2+)

1. Convert free → paid
2. Target 10-20% conversion rate
3. Launch course on Gumroad
4. Scale to 500+ users

## Free vs Paid Comparison

| Feature | Free | Pro | VIP |
|---------|------|-----|-----|
| Signals/day | 3 | Unlimited | Unlimited |
| Delivery | 15 min delay | Instant | Instant |
| Charts | Blurred | Full | Full |
| Entry/SL/TP | Basic | Full | Full |
| Risk mgmt | No | No | Yes |
| Course | No | No | Yes |
| Support | No | No | Priority |

## Anti-Sharing Measures

1. **License keys** tied to Telegram user ID
2. **Signal delay** for free tier
3. **Blurred charts** for free tier
4. **Daily limits** for free tier
5. **Key validation** on each scan (future)

## Code Reference

Subscription system: `subscriptions.py`  
Stripe webhook: `stripe_webhook.py`  
User management: `user_manager.py`  
Commands: `commands.py:/subscribe`
