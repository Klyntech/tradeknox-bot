"""
Trading Signal Bot — Configuration
All environment variables and constants live here.
"""

import os
import sys
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    # ── Telegram ────────────────────────────────────────────────────────────
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN")
    PRIVATE_CHANNEL_ID: str = os.getenv("PRIVATE_CHANNEL_ID", "-100XXXXXXXXX")
    PUBLIC_CHANNEL_ID: str = os.getenv("PUBLIC_CHANNEL_ID", "")     # optional
    PUBLIC_DELAY_MINUTES: int = 15                                    # anti-leak delay

    # ── Data Source ─────────────────────────────────────────────────────────
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "yfinance")          # yfinance | ccxt | metaapi
    METAAPI_TOKEN: str = os.getenv("METAAPI_TOKEN", "")
    METAAPI_ACCOUNT_ID: str = os.getenv("METAAPI_ACCOUNT_ID", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

    # ── Instruments ─────────────────────────────────────────────────────────
    SYMBOLS: List[str] = field(default_factory=lambda: [
        "XAUUSD", "GBPJPY"
    ])
    PRIMARY_TIMEFRAME: str = "1h"
    CONFIRM_TIMEFRAME: str = "15m"
    HTF_TIMEFRAME: str = "4h"
    STRATEGY_TIMEFRAME: str = "4h"

    # ── Market Sessions (UTC) ────────────────────────────────────────────────
    SESSIONS = {
        "asia":    {"start": 0,  "end": 8},
        "london":  {"start": 7,  "end": 16},
        "new_york":{"start": 12, "end": 21},
        "overlap": {"start": 12, "end": 16},
    }
    ALLOWED_SESSIONS: List[str] = field(default_factory=lambda: [
        "london", "new_york", "overlap"
    ])

    # ── Scoring & Confidence ─────────────────────────────────────────────────
    SCORE_WEIGHTS = {
        "market_structure":  5,
        "entry_zone":        4,
        "indicators":        3,
        "strategy_confluence": 3,
        "session_timing":    3,
        "news_clear":        2,
    }
    MIN_SCORE_THRESHOLD: int = 11
    MIN_CONFIDENCE_PCT: float = 55.0

    # ── Strategy Parameters ──────────────────────────────────────────────────
    MA_FAST_PERIOD: int = 50
    MA_SLOW_PERIOD: int = 200
    BREAKOUT_LOOKBACK: int = 20
    BREAKOUT_VOLUME_MULT: float = 1.5

    # ── Risk Management ──────────────────────────────────────────────────────
    ACCOUNT_BALANCE: float = float(os.getenv("ACCOUNT_BALANCE", "10000"))
    DEFAULT_RISK_PCT: float = 1.0
    MIN_RR_RATIO: float = 1.5
    ATR_SL_MULTIPLIER: float = 1.5
    MAX_TRADES_PER_SESSION: int = 3
    MAX_TRADES_PER_DAY: int = 5

    # ── Technical Parameters ─────────────────────────────────────────────────
    ATR_PERIOD: int = 14
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0
    EMA_FAST: int = 21
    EMA_SLOW: int = 50
    EMA_TREND: int = 200
    OB_LOOKBACK: int = 20
    FVG_MIN_SIZE_ATR: float = 0.3
    FIB_LEVELS: List[float] = field(default_factory=lambda: [0.5, 0.618, 0.786])

    # ── News Filter ──────────────────────────────────────────────────────────
    NEWS_BLACKOUT_BEFORE_MIN: int = 30
    NEWS_BLACKOUT_AFTER_MIN: int = 15

    # ── TP Levels (ATR-based) ─────────────────────────────────────────────────
    TP1_ATR_MULT: float = 1.5
    TP2_ATR_MULT: float = 2.5
    TP3_ATR_MULT: float = 3.5

    # ── Database ───────────────────────────────────────────────────────────
    TRADES_DB_PATH: str = os.getenv("TRADES_DB_PATH", "trades.db")
    LICENSES_DB_PATH: str = os.getenv("LICENSES_DB_PATH", "licenses.db")

    # ── Scan interval ────────────────────────────────────────────────────────
    SCAN_INTERVAL_SECONDS: int = 300

    # ── Chart Generation ───────────────────────────────────────────────────
    CHART_CANDLE_COUNT: int = 100
    CHART_TIMEFRAME: str = "1h"
    CHART_BLUR_ENABLED: bool = True

    # ── Stripe ──────────────────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_PRO: str = os.getenv("STRIPE_PRICE_PRO", "")
    STRIPE_PRICE_VIP: str = os.getenv("STRIPE_PRICE_VIP", "")

    # ── License ─────────────────────────────────────────────────────────────
    LICENSE_SECRET: str = os.getenv("LICENSE_SECRET", "")

    def validate(self) -> List[str]:
        """
        Validate configuration. Returns list of error messages.
        Empty list = valid config.
        """
        errors = []

        # Telegram — required for production
        if self.TELEGRAM_TOKEN in ("YOUR_BOT_TOKEN", ""):
            errors.append("TELEGRAM_TOKEN is not set (required for production)")
        if self.PRIVATE_CHANNEL_ID in ("-100XXXXXXXXX", ""):
            errors.append("PRIVATE_CHANNEL_ID is not set (required for signal delivery)")

        # Stripe — required for payments
        if not self.STRIPE_SECRET_KEY:
            errors.append("STRIPE_SECRET_KEY is not set (required for payments)")
        if not self.STRIPE_WEBHOOK_SECRET:
            errors.append("STRIPE_WEBHOOK_SECRET is not set (required for webhook security)")

        # Numeric validation
        if self.ACCOUNT_BALANCE <= 0:
            errors.append(f"ACCOUNT_BALANCE must be > 0, got {self.ACCOUNT_BALANCE}")
        if self.MIN_SCORE_THRESHOLD < 0 or self.MIN_SCORE_THRESHOLD > 20:
            errors.append(f"MIN_SCORE_THRESHOLD must be 0-20, got {self.MIN_SCORE_THRESHOLD}")
        if not (0 < self.MIN_CONFIDENCE_PCT <= 100):
            errors.append(f"MIN_CONFIDENCE_PCT must be 0-100, got {self.MIN_CONFIDENCE_PCT}")
        if self.SCAN_INTERVAL_SECONDS < 60:
            errors.append(f"SCAN_INTERVAL_SECONDS must be >= 60, got {self.SCAN_INTERVAL_SECONDS}")
        if self.MAX_TRADES_PER_DAY < 1:
            errors.append(f"MAX_TRADES_PER_DAY must be >= 1, got {self.MAX_TRADES_PER_DAY}")

        # Data source validation
        valid_sources = ("yfinance", "ccxt", "metaapi")
        if self.DATA_SOURCE not in valid_sources:
            errors.append(f"DATA_SOURCE must be one of {valid_sources}, got '{self.DATA_SOURCE}'")

        return errors

    def validate_or_exit(self):
        """Validate config and exit with clear error messages if critical vars are missing."""
        errors = self.validate()
        if not errors:
            return True

        # Separate critical (blocks startup) from warnings
        critical = [e for e in errors if "TELEGRAM_TOKEN" in e or "PRIVATE_CHANNEL_ID" in e]
        warnings = [e for e in errors if e not in critical]

        if warnings:
            for w in warnings:
                logger.warning(f"Config warning: {w}")

        if critical and self.TELEGRAM_TOKEN not in ("YOUR_BOT_TOKEN", ""):
            # Token is set but something else is wrong — warn only
            for c in critical:
                logger.warning(f"Config issue: {c}")
            return True

        if critical:
            logger.error("=== CONFIGURATION ERRORS ===")
            for c in critical:
                logger.error(f"  ✗ {c}")
            logger.error("")
            logger.error("Set these environment variables before starting the bot.")
            logger.error("Example: export TELEGRAM_TOKEN=your_bot_token_here")
            return False

        return True


CONFIG = BotConfig()
