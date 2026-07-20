"""
TradeKnox — Single-Process Entry Point

Runs Flask (health check) + Telegram bot in one process.
Flask runs in a background thread; Telegram polling runs on main thread.
"""

import logging
import os
import threading

_logger = logging.getLogger(__name__)


def start_flask():
    """Run Flask in a background thread for health checks."""
    from health_server import app
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def main():
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    _logger.info("Flask health server started")

    from bot import run_bot_with_commands
    run_bot_with_commands()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[sentry_logging],
            traces_sample_rate=0.1,
        )
        _logger.info("Sentry error tracking initialized")

    main()
