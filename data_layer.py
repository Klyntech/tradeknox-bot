"""
Layer 1: Data Layer
Handles price feeds, OHLCV data, timeframe management, session awareness.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def get_current_session(config) -> str:
    """Return the active trading session name or 'dead_zone'."""
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour

    # Overlap takes priority
    ov = config.SESSIONS["overlap"]
    if ov["start"] <= hour < ov["end"]:
        return "overlap"

    for name, window in config.SESSIONS.items():
        if name == "overlap":
            continue
        if window["start"] <= hour < window["end"]:
            return name

    return "dead_zone"


def is_session_allowed(config) -> bool:
    session = get_current_session(config)
    return session in config.ALLOWED_SESSIONS


def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 300,
                source: str = "yfinance") -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data. Returns a DataFrame with columns:
    [open, high, low, close, volume] indexed by datetime (UTC).
    """
    try:
        if source == "yfinance":
            return _fetch_yfinance(symbol, timeframe, limit)
        elif source == "ccxt":
            return _fetch_ccxt(symbol, timeframe, limit)
        else:
            logger.warning(f"Unknown source '{source}', falling back to yfinance")
            return _fetch_yfinance(symbol, timeframe, limit)
    except Exception as e:
        logger.error(f"Data fetch failed for {symbol} {timeframe}: {e}")
        return None


def _fetch_yfinance(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Fetch via yfinance — good for FOREX/Gold/indices."""
    import yfinance as yf

    TF_MAP = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "4h": "1h",  # yfinance has no 4h; we resample
        "1d": "1d",
    }
    interval = TF_MAP.get(timeframe, "1h")

    # Symbol mapping for yfinance
    YF_SYMBOLS = {
        "XAUUSD": "GC=F",
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "GBPJPY": "GBPJPY=X",
    }
    yf_symbol = YF_SYMBOLS.get(symbol, symbol)

    # Determine period based on limit + timeframe
    period_map = {
        "1m": "7d", "5m": "60d", "15m": "60d",
        "30m": "60d", "1h": "730d", "1d": "5y",
    }
    period = period_map.get(interval, "60d")

    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"No data returned for {symbol}")

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.dropna().tail(limit)

    # Resample to 4h if needed
    if timeframe == "4h":
        df = df.resample("4h").agg({
            "open": "first", "high": "max",
            "low": "min", "close": "last", "volume": "sum"
        }).dropna().tail(limit)

    return df


def _fetch_ccxt(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Fetch via CCXT — good for crypto."""
    import ccxt
    exchange = ccxt.binance({"enableRateLimit": True})
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.set_index("timestamp", inplace=True)
    return df


def sync_timeframes(symbol: str, config) -> Dict[str, pd.DataFrame]:
    """
    Fetch primary, confirmation, and HTF timeframes in one call.
    Returns dict keyed by timeframe name.
    """
    frames = {}
    for tf in [config.HTF_TIMEFRAME, config.PRIMARY_TIMEFRAME, config.CONFIRM_TIMEFRAME]:
        df = fetch_ohlcv(symbol, tf, limit=300, source=config.DATA_SOURCE)
        if df is not None and len(df) >= 50:
            frames[tf] = df
        else:
            logger.warning(f"Insufficient data for {symbol} {tf}")

    return frames


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - close).abs(),
        (low - close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def add_indicators(df: pd.DataFrame, config) -> pd.DataFrame:
    """
    Add all technical indicators to the DataFrame in-place.
    Columns added: atr, rsi, ema_fast, ema_slow, ema_trend, volume_sma, rvol
    """
    df = df.copy()

    # ATR
    df["atr"] = compute_atr(df, config.ATR_PERIOD)

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0).ewm(span=config.RSI_PERIOD, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(span=config.RSI_PERIOD, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - 100 / (1 + rs)

    # EMAs
    df["ema_fast"] = df["close"].ewm(span=config.EMA_FAST, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=config.EMA_SLOW, adjust=False).mean()
    df["ema_trend"] = df["close"].ewm(span=config.EMA_TREND, adjust=False).mean()

    # Volume SMA + RVOL (relative volume)
    df["volume_sma"] = df["volume"].rolling(20).mean()
    df["rvol"] = df["volume"] / df["volume_sma"].replace(0, np.nan)

    return df.dropna(subset=["atr", "rsi", "ema_trend"])
