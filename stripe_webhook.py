"""
Stripe Webhook Handler — Flask app for Stripe Checkout + Webhooks

Handles:
- Creating Stripe Checkout sessions for Pro/VIP subscriptions
- Processing webhook events (payment success, subscription updates)
- Generating license keys after successful payment
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta

from flask import Flask, request, jsonify

import stripe
from subscriptions import generate_license_key, TIER_DURATIONS
from user_manager import UserManager

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Stripe config
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_VIP_PRICE_ID = os.getenv("STRIPE_VIP_PRICE_ID", "")

# Domain for success/cancel URLs
DOMAIN = os.getenv("DOMAIN", "http://localhost:5000")

# Telegram config (for sending license keys)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# User manager
user_mgr = UserManager()


def _send_telegram_message(chat_id: str, text: str):
    """Send a Telegram message using requests (sync, for Flask context)."""
    if not TELEGRAM_TOKEN or not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        import requests as req
        resp = req.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }, timeout=10)
        if not resp.ok:
            logger.error(f"Telegram send failed: {resp.text}")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")


@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "TradeKnox Subscription API"})


@app.route("/health")
def health():
    """Health check endpoint for uptime monitoring."""
    import sqlite3
    from datetime import datetime, timezone

    checks = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }

    # Database check
    try:
        db_path = os.getenv("TRADES_DB_PATH", "trades.db")
        with sqlite3.connect(db_path, timeout=5) as conn:
            conn.execute("SELECT 1")
        checks["checks"]["database"] = "ok"
    except Exception as e:
        checks["checks"]["database"] = f"error: {e}"
        checks["status"] = "degraded"

    # Stripe config check
    if stripe.api_key:
        checks["checks"]["stripe"] = "ok"
    else:
        checks["checks"]["stripe"] = "not_configured"

    # Telegram config check
    if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_BOT_TOKEN":
        checks["checks"]["telegram"] = "ok"
    else:
        checks["checks"]["telegram"] = "not_configured"

    # Webhook secret check
    if STRIPE_WEBHOOK_SECRET:
        checks["checks"]["webhook_secret"] = "ok"
    else:
        checks["checks"]["webhook_secret"] = "not_set"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "ok" else 503
    return jsonify(checks), status_code


@app.route("/create-checkout", methods=["POST"])
def create_checkout():
    """
    Create a Stripe Checkout session.
    Body: { "user_id": "12345", "tier": "pro" | "vip" }
    """
    data = request.get_json()
    user_id = data.get("user_id")
    tier = data.get("tier")

    if not user_id or tier not in ("pro", "vip"):
        return jsonify({"error": "Invalid request"}), 400

    price_id = STRIPE_PRO_PRICE_ID if tier == "pro" else STRIPE_VIP_PRICE_ID
    if not price_id:
        return jsonify({"error": "Price not configured"}), 500

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{DOMAIN}/cancel",
            metadata={
                "user_id": user_id,
                "tier": tier,
            },
        )
        return jsonify({"url": session.url, "session_id": session.id})
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    if not STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook secret not configured — rejecting webhook")
        return jsonify({"error": "Webhook secret not configured"}), 500

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400

    # Handle events
    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"])
    elif event["type"] == "invoice.payment_succeeded":
        _handle_payment_succeeded(event["data"]["object"])
    elif event["type"] == "invoice.payment_failed":
        _handle_payment_failed(event["data"]["object"])
    elif event["type"] == "customer.subscription.deleted":
        _handle_subscription_deleted(event["data"]["object"])

    return jsonify({"received": True})


def _handle_checkout_completed(session: dict):
    """Generate license key after successful checkout."""
    user_id = session.get("metadata", {}).get("user_id")
    tier = session.get("metadata", {}).get("tier")
    customer_id = session.get("customer")

    if not user_id or not tier:
        logger.error("Missing user_id or tier in checkout session metadata")
        return

    # Generate license key
    key = generate_license_key(user_id, tier, TIER_DURATIONS[tier])
    expires = datetime.now(timezone.utc) + timedelta(days=TIER_DURATIONS[tier])

    # Save to database
    user_mgr.db.save_license(user_id, tier, key, expires.isoformat())
    user_mgr.db.upsert_user(
        user_id, tier=tier, license_key=key,
        stripe_customer_id=customer_id,
    )

    logger.info(f"License generated for {user_id}: {tier} -> {key}")

    # Send license key to user via Telegram
    price = "29" if tier == "pro" else "49"
    msg = (
        f"*Payment received!*\n\n"
        f"Your *{tier.upper()}* plan is now active.\n\n"
        f"License key:\n`{key}`\n\n"
        f"Use /key `{key}` to activate, or /status to verify.\n\n"
        f"_This key is tied to your account. Do not share it._"
    )
    _send_telegram_message(user_id, msg)


def _handle_payment_succeeded(invoice: dict):
    """Extend subscription on successful renewal."""
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    user = user_mgr.get_user_by_stripe_customer_id(customer_id)
    if not user:
        logger.warning(f"Payment succeeded but no user found for customer={customer_id}")
        return

    user_id = user["user_id"]
    tier = user.get("tier", "pro")

    # Generate new key with extended expiry
    key = generate_license_key(user_id, tier, TIER_DURATIONS[tier])
    expires = datetime.now(timezone.utc) + timedelta(days=TIER_DURATIONS[tier])

    user_mgr.db.save_license(user_id, tier, key, expires.isoformat())
    user_mgr.db.upsert_user(user_id, tier=tier, license_key=key)

    logger.info(f"Subscription renewed for {user_id}: {tier} -> {key}")

    msg = (
        f"*Subscription renewed!*\n\n"
        f"Your *{tier.upper()}* plan has been extended.\n"
        f"New expiry: {expires.strftime('%Y-%m-%d')}\n\n"
        f"New key:\n`{key}`"
    )
    _send_telegram_message(user_id, msg)


def _handle_payment_failed(invoice: dict):
    """Handle failed payment — notify user, grace period before downgrade."""
    customer_id = invoice.get("customer")
    attempt = invoice.get("attempt_count", 1)

    user = user_mgr.get_user_by_stripe_customer_id(customer_id)
    if not user:
        logger.warning(f"Payment failed but no user found for customer={customer_id}")
        return

    user_id = user["user_id"]
    tier = user.get("tier", "pro")

    logger.warning(f"Payment failed for {user_id} (attempt {attempt})")

    if attempt >= 3:
        # Final attempt failed — downgrade
        user_mgr.db.revoke_license(user_id)
        user_mgr.db.upsert_user(user_id, tier="free")
        msg = (
            f"*Subscription cancelled*\n\n"
            f"Payment failed after {attempt} attempts.\n"
            f"Your plan has been downgraded to *FREE*.\n\n"
            f"Use /subscribe to renew."
        )
    else:
        msg = (
            f"*Payment failed*\n\n"
            f"Attempt {attempt} of 3.\n"
            f"Please update your payment method.\n"
            f"Your plan will remain active until all attempts are exhausted.\n\n"
            f"Use /subscribe to renew."
        )
    _send_telegram_message(user_id, msg)


def _handle_subscription_deleted(subscription: dict):
    """Downgrade user to free when subscription is cancelled."""
    customer_id = subscription.get("customer")

    user = user_mgr.get_user_by_stripe_customer_id(customer_id)
    if not user:
        logger.warning(f"Subscription deleted but no user found for customer={customer_id}")
        return

    user_id = user["user_id"]

    user_mgr.db.revoke_license(user_id)
    user_mgr.db.upsert_user(user_id, tier="free")

    logger.info(f"Subscription cancelled for {user_id} — downgraded to free")

    msg = (
        f"*Subscription cancelled*\n\n"
        f"Your plan has been downgraded to *FREE*.\n"
        f"You'll receive up to 3 signals/day with a 15-min delay.\n\n"
        f"Use /subscribe to renew."
    )
    _send_telegram_message(user_id, msg)


@app.route("/success")
def success():
    return """
    <html>
    <head><title>TradeKnox - Payment Successful</title></head>
    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h1>Payment Successful!</h1>
        <p>Your license key has been generated.</p>
        <p>Check your Telegram for the key, or use /status in the bot.</p>
        <p><a href="https://t.me/TradeKnoxBot">Open TradeKnox Bot</a></p>
    </body>
    </html>
    """


@app.route("/cancel")
def cancel():
    return """
    <html>
    <head><title>TradeKnox - Payment Cancelled</title></head>
    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h1>Payment Cancelled</h1>
        <p>No charges were made.</p>
        <p><a href="https://t.me/TradeKnoxBot">Back to TradeKnox Bot</a></p>
    </body>
    </html>
    """


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)
