"""
TradeKnox Web Service — Flask app for health checks and landing page.

The bot is 100% free. No Stripe, no subscriptions, no license keys.
This Flask app serves the landing page, health check, and price proxy.
The Telegram bot runs on the main thread.
"""

import logging
import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify

logger = logging.getLogger(__name__)

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")


@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "TradeKnox Signal Bot"})


@app.route("/health")
def health():
    """Health check endpoint for uptime monitoring."""
    checks = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }

    try:
        db_path = os.getenv("TRADES_DB_PATH", "trades.db")
        with sqlite3.connect(db_path, timeout=5) as conn:
            conn.execute("SELECT 1")
        checks["checks"]["database"] = "ok"
    except Exception as e:
        checks["checks"]["database"] = f"error: {e}"
        checks["status"] = "degraded"

    if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_BOT_TOKEN":
        checks["checks"]["telegram"] = "ok"
    else:
        checks["checks"]["telegram"] = "not_configured"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "ok" else 503
    return jsonify(checks), status_code


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)
