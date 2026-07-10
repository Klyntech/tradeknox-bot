"""
Strategy Tester — Per Day of Week
Tests each strategy's performance broken down by day of week.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "AUDUSD", "NZDUSD", "USDCAD"]
TIMEFRAMES = ["15m", "1h", "4h", "1d"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_data(symbol: str, timeframe: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{symbol}_{timeframe}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, index_col=0, parse_dates=True)


def strategy_ma_crossover(df, fast, slow):
    df = df.copy()
    col_f, col_s = f"ema_{fast}", f"ema_{slow}"
    if col_f not in df.columns or col_s not in df.columns:
        df["signal"] = 0
        return df
    f, s = df[col_f], df[col_s]
    df["signal"] = 0
    df.loc[(f.shift(1) <= s.shift(1)) & (f > s), "signal"] = 1
    df.loc[(f.shift(1) >= s.shift(1)) & (f < s), "signal"] = -1
    return df


def strategy_breakout(df, lookback):
    df = df.copy()
    df["signal"] = 0
    high_n = df["high"].rolling(lookback).max().shift(1)
    low_n = df["low"].rolling(lookback).min().shift(1)
    df.loc[df["close"] > high_n, "signal"] = 1
    df.loc[df["close"] < low_n, "signal"] = -1
    return df


def strategy_rsi_extremes(df, oversold, overbought):
    df = df.copy()
    df["signal"] = 0
    df.loc[df["rsi"] < oversold, "signal"] = 1
    df.loc[df["rsi"] > overbought, "signal"] = -1
    return df


def strategy_ema_alignment(df):
    df = df.copy()
    df["signal"] = 0
    bullish = (df["ema_9"] > df["ema_21"]) & (df["ema_21"] > df["ema_50"]) & (df["close"] > df["ema_200"])
    bearish = (df["ema_9"] < df["ema_21"]) & (df["ema_21"] < df["ema_50"]) & (df["close"] < df["ema_200"])
    df.loc[bullish, "signal"] = 1
    df.loc[bearish, "signal"] = -1
    return df


def backtest_by_day(df, signal_col="signal", rr_ratio=1.5, max_hold=24):
    """Backtest and break results down by day of week."""
    day_trades = {d: [] for d in DAYS}

    i = 0
    while i < len(df) - 1:
        signal = df[signal_col].iloc[i]
        if signal == 0:
            i += 1
            continue

        entry = df["open"].iloc[i + 1]
        direction = "buy" if signal == 1 else "sell"
        atr = df["atr"].iloc[i] if not pd.isna(df["atr"].iloc[i]) else entry * 0.005
        sl_distance = atr * 1.5
        tp_distance = sl_distance * rr_ratio

        if direction == "buy":
            sl, tp = entry - sl_distance, entry + tp_distance
        else:
            sl, tp = entry + sl_distance, entry - tp_distance

        result = "open"
        for j in range(i + 2, min(i + 2 + max_hold, len(df))):
            c = df.iloc[j]
            if direction == "buy":
                if c["low"] <= sl:
                    result = "loss"; break
                if c["high"] >= tp:
                    result = "win"; break
            else:
                if c["high"] >= sl:
                    result = "loss"; break
                if c["low"] <= tp:
                    result = "win"; break

        # Get day of week from signal candle
        day_name = df.index[i].day_name()
        if day_name in day_trades:
            day_trades[day_name].append(1 if result == "win" else -1 if result == "loss" else 0)

        i += 1

    # Compute stats per day
    results = {}
    for day in DAYS:
        trades = [t for t in day_trades[day] if t != 0]
        if not trades:
            results[day] = {"trades": 0, "win_rate": 0, "profit_factor": 0, "net_pips": 0}
            continue

        wins = sum(1 for t in trades if t == 1)
        losses = sum(1 for t in trades if t == -1)
        win_rate = wins / len(trades) * 100

        gross_profit = wins * rr_ratio
        gross_loss = losses * 1.0
        pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        net = wins * rr_ratio - losses

        results[day] = {
            "trades": len(trades),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(pf, 2),
            "net_pips": round(net, 2),
        }

    return results


STRATEGIES = [
    ("ma_9_21", lambda df: strategy_ma_crossover(df, 9, 21), "MA 9/21"),
    ("ma_21_50", lambda df: strategy_ma_crossover(df, 21, 50), "MA 21/50"),
    ("ma_50_200", lambda df: strategy_ma_crossover(df, 50, 200), "MA 50/200"),
    ("breakout_10", lambda df: strategy_breakout(df, 10), "Breakout 10"),
    ("breakout_20", lambda df: strategy_breakout(df, 20), "Breakout 20"),
    ("breakout_50", lambda df: strategy_breakout(df, 50), "Breakout 50"),
    ("rsi_20_80", lambda df: strategy_rsi_extremes(df, 20, 80), "RSI 20/80"),
    ("rsi_25_75", lambda df: strategy_rsi_extremes(df, 25, 75), "RSI 25/75"),
    ("rsi_30_70", lambda df: strategy_rsi_extremes(df, 30, 70), "RSI 30/70"),
    ("ema_alignment", strategy_ema_alignment, "EMA Align"),
]


def main():
    print("=" * 90)
    print("Strategy Performance by Day of Week")
    print("=" * 90)

    all_results = []

    for tf in ["4h"]:  # Focus on 4h (best from research)
        for symbol in SYMBOLS:
            df = load_data(symbol, tf)
            if df.empty or len(df) < 200:
                continue

            for strat_id, strat_func, strat_name in STRATEGIES:
                try:
                    df_strat = strat_func(df.copy())
                    results = backtest_by_day(df_strat)

                    for day, stats in results.items():
                        if stats["trades"] > 0:
                            all_results.append({
                                "symbol": symbol,
                                "timeframe": tf,
                                "strategy": strat_name,
                                "day": day,
                                "trades": stats["trades"],
                                "win_rate": stats["win_rate"],
                                "profit_factor": stats["profit_factor"],
                                "net_pips": stats["net_pips"],
                            })
                except Exception as e:
                    pass

    df_all = pd.DataFrame(all_results)

    # Save
    csv_path = os.path.join(DATA_DIR, "strategy_by_day.csv")
    df_all.to_csv(csv_path, index=False)

    # Print best day per strategy per symbol
    print(f"\n{'='*90}")
    print("  BEST DAY PER STRATEGY PER SYMBOL (4h)")
    print(f"{'='*90}")
    print(f"  {'Symbol':<8} {'Strategy':<15} {'Best Day':<12} {'Trades':<7} {'WR':<7} {'PF':<7} {'Net':<8}")
    print(f"  {'-'*60}")

    for symbol in SYMBOLS:
        sym_df = df_all[df_all["symbol"] == symbol]
        for strat_name in df_all["strategy"].unique():
            strat_df = sym_df[sym_df["strategy"] == strat_name]
            if strat_df.empty:
                continue
            best = strat_df.sort_values("profit_factor", ascending=False).iloc[0]
            if best["trades"] >= 5:  # minimum 5 trades
                print(f"  {symbol:<8} {strat_name:<15} {best['day']:<12} {best['trades']:<7} "
                      f"{best['win_rate']:<7} {best['profit_factor']:<7} {best['net_pips']:<8}")

    # Print worst day per strategy per symbol
    print(f"\n{'='*90}")
    print("  WORST DAY PER STRATEGY PER SYMBOL (4h)")
    print(f"{'='*90}")
    print(f"  {'Symbol':<8} {'Strategy':<15} {'Worst Day':<12} {'Trades':<7} {'WR':<7} {'PF':<7} {'Net':<8}")
    print(f"  {'-'*60}")

    for symbol in SYMBOLS:
        sym_df = df_all[df_all["symbol"] == symbol]
        for strat_name in df_all["strategy"].unique():
            strat_df = sym_df[sym_df["strategy"] == strat_name]
            if strat_df.empty:
                continue
            worst = strat_df.sort_values("profit_factor", ascending=True).iloc[0]
            if worst["trades"] >= 5:
                print(f"  {symbol:<8} {strat_name:<15} {worst['day']:<12} {worst['trades']:<7} "
                      f"{worst['win_rate']:<7} {worst['profit_factor']:<7} {worst['net_pips']:<8}")

    # Full table
    print(f"\n{'='*90}")
    print("  FULL RESULTS (sorted by profit factor)")
    print(f"{'='*90}")
    print(f"  {'Symbol':<8} {'Strategy':<15} {'Day':<12} {'Trades':<7} {'WR':<7} {'PF':<7} {'Net':<8}")
    print(f"  {'-'*60}")

    df_sorted = df_all.sort_values(["symbol", "strategy", "profit_factor"], ascending=[True, True, False])
    for _, row in df_sorted.iterrows():
        if row["trades"] >= 5:
            marker = " ***" if row["profit_factor"] >= 1.5 else ""
            print(f"  {row['symbol']:<8} {row['strategy']:<15} {row['day']:<12} {row['trades']:<7} "
                  f"{row['win_rate']:<7} {row['profit_factor']:<7} {row['net_pips']:<8}{marker}")

    print(f"\nResults saved to {csv_path}")


if __name__ == "__main__":
    main()
