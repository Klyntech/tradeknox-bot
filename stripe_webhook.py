"""
TradeKnox Web Service — Flask app for health checks and landing page.

The bot is 100% free. No Stripe, no subscriptions, no license keys.
This Flask app serves the landing page, health check, and price proxy.
The Telegram bot runs on the main thread.
"""

import logging
import os
import sqlite3
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, send_from_directory

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=None)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")

_price_cache = {"data": None, "ts": 0}


@app.route("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.route("/prices")
def prices():
    """Proxy Twelve Data batch quote — cached 30s, no API key exposed."""
    now = time.time()
    if _price_cache["data"] and now - _price_cache["ts"] < 30:
        return jsonify(_price_cache["data"])

    if not TWELVEDATA_API_KEY:
        return jsonify({"error": "no api key"}), 503

    try:
        import requests
        symbols = "XAUUSD,EURUSD,GBPUSD,USDJPY,AUDUSD,GBPJPY"
        r = requests.get(
            f"https://api.twelvedata.com/quote",
            params={"symbol": symbols, "apikey": TWELVEDATA_API_KEY},
            timeout=5,
        )
        raw = r.json()
        out = {}
        for sym, val in raw.items():
            if isinstance(val, dict) and "percent_change" in val:
                out[sym] = {
                    "p": float(val.get("close", 0)),
                    "c": float(val.get("percent_change", 0)),
                }
        if out:
            _price_cache["data"] = out
            _price_cache["ts"] = now
        return jsonify(out)
    except Exception as e:
        logger.warning(f"Price fetch failed: {e}")
        return jsonify({"error": str(e)}), 500


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
