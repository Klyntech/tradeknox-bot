#!/usr/bin/env python3
"""
TradeKnox Backtest Script — Multi-Strategy
Backtests all strategies on downloaded data (yfinance + Dukascopy).

Usage:
    python scripts/backtest_strategies.py                    # Backtest all pairs
    python scripts/backtest_strategies.py --pair XAUUSD      # Backtest specific pair
    python scripts/backtest_strategies.py --source yfinance  # Use yfinance data only
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies import (
    detect_ma_crossover,
    detect_breakout,
    detect_rsi_extremes,
    detect_ema_crossover,
    detect_heikin_ashi_trend,
    detect_stochastic_extreme,
    PAIR_STRATEGIES,
)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
YFINANCE_DIR = DATA_DIR / "yfinance"
DUKASCOPY_DIR = DATA_DIR / "dukascopy"

PAIRS = ["XAUUSD", "GBPJPY", "EURUSD", "GBPUSD", "USDJPY"]


def load_data(source_dir: Path, pair: str, interval: str) -> pd.DataFrame:
    """Load data from CSV file."""
    filename = f"{pair}_{interval}.csv"
    filepath = source_dir / filename

    if not filepath.exists():
        print(f"  WARNING: File not found: {filepath}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        print(f"  Loaded {len(df)} rows from {filepath.name}")
        return df
    except Exception as e:
        print(f"  ERROR loading {filepath}: {e}")
        return pd.DataFrame()


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators needed for strategies."""
    # ATR
    if "atr" not in df.columns:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = true_range.rolling(window=14).mean()

    # RSI
    if "rsi" not in df.columns:
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

    # EMAs
    for period in [9, 21, 50, 100, 200]:
        col = f"ema_{period}"
        if col not in df.columns:
            df[col] = df["close"].ewm(span=period, adjust=False).mean()

    return df


def backtest_strategy(df: pd.DataFrame, strategy_name: str, direction: str, pair: str) -> dict:
    """Backtest a single strategy on historical data."""
    if len(df) < 100:
        return {"trades": 0, "wins": 0, "losses": 0, "win_rate": 0, "pf": 0}

    trades = []
    entry_price = None
    entry_direction = None

    for i in range(50, len(df)):
        window = df.iloc[:i+1]
        current_price = window["close"].iloc[-1]

        # Get signal based on strategy
        signal = None
        if strategy_name == "ma_crossover":
            sig = detect_ma_crossover(window, fast_period=9, slow_period=21)
            signal = sig.direction
        elif strategy_name == "breakout":
            sig = detect_breakout(window, lookback=10)
            signal = sig.direction
        elif strategy_name == "rsi_extremes":
            sig = detect_rsi_extremes(window, oversold=20, overbought=80)
            signal = sig.direction
        elif strategy_name == "ema_crossover":
            sig = detect_ema_crossover(window, fast_period=9, slow_period=21, trend_period=100)
            signal = sig.direction
        elif strategy_name == "heikin_ashi":
            sig = detect_heikin_ashi_trend(window)
            signal = sig.direction
        elif strategy_name == "stochastic":
            sig = detect_stochastic_extreme(window)
            signal = sig.direction

        # Entry logic
        if entry_price is None and signal == direction:
            entry_price = current_price
            entry_direction = direction
            entry_idx = i

        # Exit logic (simple: 1% take profit or stop loss)
        elif entry_price is not None:
            if direction == "bullish":
                pnl_pct = (current_price - entry_price) / entry_price * 100
            else:
                pnl_pct = (entry_price - current_price) / entry_price * 100

            # Take profit or stop loss
            if pnl_pct >= 1.0 or pnl_pct <= -0.5:
                trades.append({
                    "entry": entry_price,
                    "exit": current_price,
                    "pnl_pct": pnl_pct,
                    "direction": direction,
                })
                entry_price = None
                entry_direction = None

    # Calculate statistics
    if not trades:
        return {"trades": 0, "wins": 0, "losses": 0, "win_rate": 0, "pf": 0}

    wins = [t for t in trades if t["pnl_pct"] > 0]
    losses = [t for t in trades if t["pnl_pct"] <= 0]

    win_rate = len(wins) / len(trades) * 100 if trades else 0

    # Profit factor
    gross_profit = sum(t["pnl_pct"] for t in wins) if wins else 0
    gross_loss = abs(sum(t["pnl_pct"] for t in losses)) if losses else 0.01
    pf = gross_profit / gross_loss if gross_loss > 0 else 0

    return {
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "pf": round(pf, 2),
        "total_return": round(sum(t["pnl_pct"] for t in trades), 2),
    }


def backtest_pair(pair: str, source: str) -> dict:
    """Backtest all strategies on a single pair."""
    print(f"\n{'='*60}")
    print(f"BACKTESTING: {pair}")
    print(f"{'='*60}")

    # Load data
    if source == "yfinance":
        df = load_data(YFINANCE_DIR, pair, "daily")
    else:
        df = load_data(DUKASCOPY_DIR, pair, "hourly")

    if df.empty:
        print(f"  No data available for {pair}")
        return {}

    # Calculate indicators
    df = calculate_indicators(df)

    # Get pair config
    config = PAIR_STRATEGIES.get(pair, PAIR_STRATEGIES["XAUUSD"])

    # Strategies to backtest
    strategies = [
        ("ma_crossover", "MA Crossover", "bullish"),
        ("breakout", "Breakout", "bullish"),
        ("rsi_extremes", "RSI Extremes", "bullish"),
        ("ema_crossover", "EMA Crossover (MM-008)", "bullish"),
        ("heikin_ashi", "Heikin Ashi Trend (MM-017)", "bullish"),
        ("stochastic", "Stochastic Extreme (MM-016)", "bullish"),
    ]

    results = {}
    for strat_name, strat_label, direction in strategies:
        print(f"\n  Testing {strat_label}...")
        result = backtest_strategy(df, strat_name, direction, pair)
        results[strat_name] = result

        print(f"    Trades: {result['trades']}")
        print(f"    Win Rate: {result['win_rate']}%")
        print(f"    Profit Factor: {result['pf']}")
        print(f"    Total Return: {result['total_return']}%")

    return results


def main():
    parser = argparse.ArgumentParser(description="Backtest TradeKnox strategies")
    parser.add_argument(
        "--pair",
        choices=PAIRS,
        default=None,
        help="Backtest specific pair (default: all)",
    )
    parser.add_argument(
        "--source",
        choices=["yfinance", "dukascopy"],
        default="yfinance",
        help="Data source to use (default: yfinance)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("TradeKnox Multi-Strategy Backtest")
    print("=" * 60)
    print(f"Source: {args.source}")
    print(f"Pairs: {args.pair if args.pair else 'All'}")

    pairs_to_test = [args.pair] if args.pair else PAIRS
    all_results = {}

    for pair in pairs_to_test:
        results = backtest_pair(pair, args.source)
        all_results[pair] = results

    # Summary report
    print(f"\n{'='*60}")
    print("BACKTEST SUMMARY")
    print(f"{'='*60}")

    for pair, results in all_results.items():
        print(f"\n{pair}:")
        for strat_name, result in results.items():
            if result["trades"] > 0:
                print(f"  {strat_name}: {result['trades']} trades, "
                      f"WR {result['win_rate']}%, PF {result['pf']}, "
                      f"Return {result['total_return']}%")

    # Save results to file
    results_path = DATA_DIR / "backtest_results.txt"
    with open(results_path, "w") as f:
        f.write("TradeKnox Backtest Results\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Source: {args.source}\n\n")

        for pair, results in all_results.items():
            f.write(f"\n{pair}:\n")
            for strat_name, result in results.items():
                f.write(f"  {strat_name}: {result}\n")

    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()
