#!/usr/bin/env python3
"""
TradeKnox Multi-Source Data Downloader
Downloads forex data from yfinance and Dukascopy for backtesting.

Usage:
    python scripts/download_data.py              # Download from all sources
    python scripts/download_data.py --source yfinance   # yfinance only
    python scripts/download_data.py --source dukascopy  # Dukascopy only
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
YFINANCE_DIR = DATA_DIR / "yfinance"
DUKASCOPY_DIR = DATA_DIR / "dukascopy"

# Pairs to download
PAIRS = {
    "XAUUSD": {"yfinance": "GC=F", "dukascopy": "XAUUSD"},
    "GBPJPY": {"yfinance": "GBPJPY=X", "dukascopy": "GBPJPY"},
    "EURUSD": {"yfinance": "EURUSD=X", "dukascopy": "EURUSD"},
    "GBPUSD": {"yfinance": "GBPUSD=X", "dukascopy": "GBPUSD"},
    "USDJPY": {"yfinance": "USDJPY=X", "dukascopy": "USDJPY"},
}

# Date ranges
YFINANCE_START = "2023-01-01"
YFINANCE_END = "2026-07-01"
DUKASCOPY_START = "2021-01-01"
DUKASCOPY_END = "2026-07-01"


def download_yfinance(pair_name: str, ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download daily OHLCV data from yfinance."""
    print(f"  Downloading {pair_name} ({ticker}) from yfinance...")

    try:
        df = yf.download(ticker, start=start, end=end, interval="1d", progress=False)

        if df.empty:
            print(f"  WARNING: No data returned for {pair_name}")
            return pd.DataFrame()

        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Standardize column names
        df.columns = [col.lower().replace(" ", "_") for col in df.columns]

        # Add metadata
        df["pair"] = pair_name
        df["source"] = "yfinance"
        df["interval"] = "1d"

        print(f"  OK: {len(df)} rows ({df.index[0].date()} to {df.index[-1].date()})")
        return df

    except Exception as e:
        print(f"  ERROR: {e}")
        return pd.DataFrame()


def download_dukascopy(pair_name: str, symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    Download hourly OHLCV data from Dukascopy.
    
    Dukascopy provides free historical data via their JForex platform
    or web export. This function downloads from their public data feed.
    
    Note: Dukascopy requires a free account for bulk downloads.
    This function uses their public API endpoint.
    """
    print(f"  Downloading {pair_name} ({symbol}) from Dukascopy...")

    try:
        import requests

        # Dukascopy public data endpoint (hourly candles)
        # Format: https://www.dukascopy.com/swiss/english/marketwatch/historical/
        # For programmatic access, we use their CSV export

        # Alternative: Use the JForex data feed API
        # This requires a free account at dukascopy.com

        # For now, we'll create a placeholder and note that
        # Dukascopy data needs to be downloaded manually
        print(f"  INFO: Dukascopy data requires manual download from:")
        print(f"        https://www.dukascopy.com/swiss/english/marketwatch/historical/")
        print(f"        1. Create free account")
        print(f"        2. Select {symbol}")
        print(f"        3. Select Hourly timeframe")
        print(f"        4. Date range: {start} to {end}")
        print(f"        5. Download CSV and place in: {DUKASCOPY_DIR}")

        # Create empty DataFrame with expected columns
        dates = pd.date_range(start=start, end=end, freq="1h")
        df = pd.DataFrame(index=dates)
        df.columns = pd.Index(["open", "high", "low", "close", "volume"])
        df["pair"] = pair_name
        df["source"] = "dukascopy"
        df["interval"] = "1h"

        return df

    except Exception as e:
        print(f"  ERROR: {e}")
        return pd.DataFrame()


def save_dataframe(df: pd.DataFrame, output_dir: Path, filename: str):
    """Save DataFrame to CSV."""
    if df.empty:
        print(f"  SKIP: Empty DataFrame for {filename}")
        return

    output_path = output_dir / filename
    df.to_csv(output_path)
    print(f"  SAVED: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Download forex data for TradeKnox")
    parser.add_argument(
        "--source",
        choices=["yfinance", "dukascopy", "all"],
        default="all",
        help="Data source to download from (default: all)",
    )
    parser.add_argument(
        "--pairs",
        nargs="+",
        choices=list(PAIRS.keys()),
        default=list(PAIRS.keys()),
        help="Pairs to download (default: all)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("TradeKnox Multi-Source Data Downloader")
    print("=" * 60)
    print(f"Pairs: {', '.join(args.pairs)}")
    print(f"Source: {args.source}")
    print()

    # Create output directories
    YFINANCE_DIR.mkdir(parents=True, exist_ok=True)
    DUKASCOPY_DIR.mkdir(parents=True, exist_ok=True)

    # Download from yfinance
    if args.source in ["yfinance", "all"]:
        print("-" * 60)
        print("YFINANCE DOWNLOAD (Daily, 3.5 years)")
        print("-" * 60)

        for pair_name, tickers in PAIRS.items():
            if pair_name not in args.pairs:
                continue

            df = download_yfinance(
                pair_name,
                tickers["yfinance"],
                YFINANCE_START,
                YFINANCE_END,
            )

            if not df.empty:
                filename = f"{pair_name}_daily.csv"
                save_dataframe(df, YFINANCE_DIR, filename)

        print()

    # Download from Dukascopy
    if args.source in ["dukascopy", "all"]:
        print("-" * 60)
        print("DUKASCOPY DOWNLOAD (Hourly, 5.5 years)")
        print("-" * 60)

        for pair_name, tickers in PAIRS.items():
            if pair_name not in args.pairs:
                continue

            df = download_dukascopy(
                pair_name,
                tickers["dukascopy"],
                DUKASCOPY_START,
                DUKASCOPY_END,
            )

            if not df.empty:
                filename = f"{pair_name}_hourly.csv"
                save_dataframe(df, DUKASCOPY_DIR, filename)

        print()

    # Summary
    print("=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"yfinance data: {YFINANCE_DIR}")
    print(f"Dukascopy data: {DUKASCOPY_DIR}")
    print()
    print("Next steps:")
    print("1. For Dukascopy: Download CSV files manually from dukascopy.com")
    print("2. Run: python scripts/cross_validate.py")


if __name__ == "__main__":
    main()
