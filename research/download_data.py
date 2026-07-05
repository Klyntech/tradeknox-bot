"""
Download Historical Data — Multi-Timeframe
Downloads 15m, 1h, 4h OHLCV for all symbols from yfinance, adds indicators, saves to CSV.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Symbol mapping for yfinance
SYMBOLS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "GBPJPY": "GBPJPY=X",
}

# Timeframes to download
TIMEFRAMES = {
    "15m": {"interval": "15m", "period": "60d"},    # yfinance limit: 60 days for 15m
    "1h":  {"interval": "1h",  "period": "max"},    # ~2 years available
    "4h":  {"interval": "1h",  "period": "max"},    # will resample to 4h
    "1d":  {"interval": "1d",  "period": "max"},    # daily from 2000
}


def download_symbol(name: str, yf_symbol: str, timeframe: str, config: dict) -> pd.DataFrame:
    """Download data for a symbol and timeframe."""
    print(f"  Downloading {name} ({yf_symbol}) [{timeframe}]...")

    ticker = yf.Ticker(yf_symbol)

    if timeframe == "4h":
        # Download 1h and resample to 4h
        df = ticker.history(period=config["period"], interval="1h")
        if df.empty:
            print(f"  WARNING: No 1h data for {name}, cannot resample to 4h")
            return pd.DataFrame()

        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df.index = pd.to_datetime(df.index, utc=True)

        # Resample to 4h
        df = df.resample("4h").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()
    else:
        df = ticker.history(period=config["period"], interval=config["interval"])
        if df.empty:
            print(f"  WARNING: No data for {name}")
            return pd.DataFrame()

        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df.index = pd.to_datetime(df.index, utc=True)

    df = df.dropna()

    if len(df) == 0:
        print(f"  WARNING: Empty data for {name} [{timeframe}]")
        return pd.DataFrame()

    print(f"  {name} [{timeframe}]: {df.index[0].date()} to {df.index[-1].date()} ({len(df)} candles)")
    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators."""
    df = df.copy()

    # ATR
    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - close_prev).abs(),
        (low - close_prev).abs()
    ], axis=1).max(axis=1)
    df["atr"] = tr.ewm(span=14, adjust=False).mean()

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0).ewm(span=14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(span=14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - 100 / (1 + rs)

    # EMAs
    df["ema_9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["ema_21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()

    # Bollinger Bands
    df["bb_mid"] = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * bb_std
    df["bb_lower"] = df["bb_mid"] - 2 * bb_std
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]

    # Volume SMA + RVOL (set to 1.0 when volume is 0, as in forex)
    df["volume_sma"] = df["volume"].rolling(20).mean()
    df["rvol"] = df["volume"] / df["volume_sma"].replace(0, np.nan)
    df["rvol"] = df["rvol"].fillna(1.0)  # No real volume → rvol = 1.0

    # Returns
    df["return_1h"] = df["close"].pct_change()
    df["return_4h"] = df["close"].pct_change(4)
    df["return_1d"] = df["close"].pct_change(24)

    # Session (UTC hour)
    df["hour"] = df.index.hour

    # Volatility (ATR as % of price)
    df["volatility"] = df["atr"] / df["close"] * 100

    return df.dropna()


def main():
    print("=" * 60)
    print("Phase 1: Downloading Historical Data (Multi-Timeframe)")
    print("=" * 60)

    for timeframe, config in TIMEFRAMES.items():
        print(f"\n--- {timeframe} ---")
        for name, yf_symbol in SYMBOLS.items():
            df = download_symbol(name, yf_symbol, timeframe, config)
            if df.empty:
                continue

            df = add_indicators(df)

            csv_path = os.path.join(DATA_DIR, f"{name}_{timeframe}.csv")
            df.to_csv(csv_path)
            print(f"  Saved: {csv_path} ({len(df)} rows)")

    print("\n" + "=" * 60)
    print("Done! Data saved to research/data/")
    print("=" * 60)

    # Summary
    print("\nSummary:")
    for tf in TIMEFRAMES:
        print(f"\n  {tf}:")
        for name in SYMBOLS:
            csv_path = os.path.join(DATA_DIR, f"{name}_{tf}.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                print(f"    {name}: {len(df)} candles")


if __name__ == "__main__":
    main()
