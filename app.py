"""
TradeKnox — Single-Process Entry Point

Runs Flask (Stripe webhooks) + Telegram bot in one process.
Flask runs in a background thread; Telegram polling runs on main thread.
"""

import logging
import threading


def start_flask():
    """Run Flask in a background thread for Stripe webhooks."""
    from stripe_webhook import app
    app.run(host="0.0.0.0", port=5000)


def main():
    # Start Flask in background
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    logging.info("Flask webhook server started on port 5000")

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
