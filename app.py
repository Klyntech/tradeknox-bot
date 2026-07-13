"""
TradeKnox — Single-Process Entry Point

Runs Flask (health check) + Telegram bot in one process.
Flask runs in a background thread; Telegram polling runs on main thread.
"""

import logging
import os
import threading
import time
import urllib.request

_logger = logging.getLogger(__name__)


def start_flask():
    """Run Flask in a background thread for health checks."""
    from stripe_webhook import app
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    """Ping ourselves every 10 minutes to prevent Render Free tier spin-down."""
    port = int(os.getenv("PORT", "5000"))
    url = f"http://localhost:{port}/health"
    while True:
        time.sleep(600)
        try:
            urllib.request.urlopen(url, timeout=10)
            _logger.info("Keep-alive ping OK")
        except Exception as e:
            _logger.warning(f"Keep-alive ping failed: {e}")


def main():
    # Start Flask in background (health endpoint only)
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    _logger.info("Flask health server started")

    # Start keep-alive to prevent Render spin-down
    alive_thread = threading.Thread(target=keep_alive, daemon=True)
    alive_thread.start()
    _logger.info("Keep-alive thread started (10 min interval)")

    # Run Telegram bot on main thread (blocking)
    from bot import run_bot_with_commands
    run_bot_with_commands()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    main()
