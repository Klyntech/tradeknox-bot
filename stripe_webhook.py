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
from typing import Optional

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

# User manager
user_mgr = UserManager()


@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "TradeKnox Subscription API"})


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
        logger.warning("Stripe webhook secret not set — skipping verification")
        event = json.loads(payload)
    else:
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

    if not user_id or not tier:
        logger.error("Missing user_id or tier in checkout session metadata")
        return

    # Generate license key
    key = generate_license_key(user_id, tier, TIER_DURATIONS[tier])
    expires = datetime.now(timezone.utc) + timedelta(days=TIER_DURATIONS[tier])

    # Save to database
    user_mgr.db.save_license(user_id, tier, key, expires.isoformat())
    user_mgr.db.upsert_user(user_id, tier=tier, license_key=key)

    logger.info(f"License generated for {user_id}: {tier} -> {key}")

    # TODO: Send license key to user via Telegram
    # This requires the bot to be running and have the user's chat_id


def _handle_payment_succeeded(invoice: dict):
    """Extend subscription on successful renewal."""
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    # TODO: Look up user by Stripe customer ID
    # For now, log the event
    logger.info(f"Payment succeeded: customer={customer_id}, sub={subscription_id}")


def _handle_payment_failed(invoice: dict):
    """Handle failed payment — could downgrade user."""
    customer_id = invoice.get("customer")
    logger.warning(f"Payment failed: customer={customer_id}")
    # TODO: Send notification to user, grace period before downgrade


def _handle_subscription_deleted(subscription: dict):
    """Downgrade user to free when subscription is cancelled."""
    customer_id = subscription.get("customer")
    logger.info(f"Subscription deleted: customer={customer_id}")
    # TODO: Find user by Stripe customer ID, downgrade to free


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
    app.run(host="0.0.0.0", port=5000, debug=True)
