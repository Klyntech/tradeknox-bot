"""
Trading Signal Bot — Configuration
All environment variables and constants live here.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class BotConfig:
    # ── Telegram ────────────────────────────────────────────────────────────
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN")
    PRIVATE_CHANNEL_ID: str = os.getenv("PRIVATE_CHANNEL_ID", "-100XXXXXXXXX")
    PUBLIC_CHANNEL_ID: str = os.getenv("PUBLIC_CHANNEL_ID", "")     # optional
    PUBLIC_DELAY_MINUTES: int = 15                                    # anti-leak delay

    # ── Data Source ─────────────────────────────────────────────────────────
    # Primary: CCXT (crypto) or MetaAPI (forex/gold) or yfinance (fallback)
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "yfinance")          # yfinance | ccxt | metaapi
    METAAPI_TOKEN: str = os.getenv("METAAPI_TOKEN", "")
    METAAPI_ACCOUNT_ID: str = os.getenv("METAAPI_ACCOUNT_ID", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")                # forexfactory or investing.com API

    # ── Instruments ─────────────────────────────────────────────────────────
    SYMBOLS: List[str] = field(default_factory=lambda: [
        "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY"
    ])
    PRIMARY_TIMEFRAME: str = "1h"       # main analysis TF
    CONFIRM_TIMEFRAME: str = "15m"      # entry confirmation TF
    HTF_TIMEFRAME: str = "4h"           # higher timeframe bias

    # ── Market Sessions (UTC) ────────────────────────────────────────────────
    SESSIONS = {
        "asia":    {"start": 0,  "end": 8},
        "london":  {"start": 7,  "end": 16},
        "new_york":{"start": 12, "end": 21},
        "overlap": {"start": 12, "end": 16},   # London–NY overlap (best)
    }
    ALLOWED_SESSIONS: List[str] = field(default_factory=lambda: [
        "london", "new_york", "overlap"
    ])

    # ── Scoring & Confidence ─────────────────────────────────────────────────
    SCORE_WEIGHTS = {
        "market_structure":  5,   # Trend + BOS/CHoCH
        "entry_zone":        4,   # OB + FVG + Fib confluence
        "indicators":        3,   # RSI + EMA + Volume
        "session_timing":    3,   # Allowed session active
        "news_clear":        2,   # No high-impact event nearby
    }
    MIN_SCORE_THRESHOLD: int = 12       # out of 17 — below this = NO TRADE
    MIN_CONFIDENCE_PCT: float = 65.0    # minimum confidence to fire signal

    # ── Risk Management ──────────────────────────────────────────────────────
    DEFAULT_RISK_PCT: float = 1.0       # % of account per trade
    MIN_RR_RATIO: float = 1.5           # minimum 1:1.5 required
    ATR_SL_MULTIPLIER: float = 1.5      # SL = ATR × multiplier
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
    OB_LOOKBACK: int = 20               # candles to look back for order blocks
    FVG_MIN_SIZE_ATR: float = 0.3       # FVG must be ≥ 0.3× ATR to count
    FIB_LEVELS: List[float] = field(default_factory=lambda: [0.5, 0.618, 0.786])

    # ── News Filter ──────────────────────────────────────────────────────────
    NEWS_BLACKOUT_BEFORE_MIN: int = 30  # block 30 min before high-impact news
    NEWS_BLACKOUT_AFTER_MIN: int = 15   # block 15 min after

    # ── TP Levels (ATR-based) ─────────────────────────────────────────────────
    TP1_ATR_MULT: float = 1.0
    TP2_ATR_MULT: float = 2.0
    TP3_ATR_MULT: float = 3.0

    # ── Scan interval ────────────────────────────────────────────────────────
    SCAN_INTERVAL_SECONDS: int = 300    # scan every 5 minutes


CONFIG = BotConfig()
