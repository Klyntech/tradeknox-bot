"""
Strategy Tester — Multi-Timeframe
Tests each strategy independently across all symbols and timeframes.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "AUDUSD", "NZDUSD", "USDCAD"]
TIMEFRAMES = ["15m", "1h", "4h", "1d"]


def load_data(symbol: str, timeframe: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{symbol}_{timeframe}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, index_col=0, parse_dates=True)


# ──────────────────────────────────────────────────────────────────────────────
# Strategy Implementations (with ACTUAL crossover detection)
# ──────────────────────────────────────────────────────────────────────────────

def strategy_ma_crossover(df: pd.DataFrame, fast: int, slow: int) -> pd.DataFrame:
    """MA Crossover: signal ONLY on actual crossover, not position."""
    df = df.copy()
    col_fast = f"ema_{fast}"
    col_slow = f"ema_{slow}"

    if col_fast not in df.columns or col_slow not in df.columns:
        df["signal"] = 0
        return df

    fast_ma = df[col_fast]
    slow_ma = df[col_slow]

    df["signal"] = 0

    # Golden Cross: fast crosses above slow
    golden = (fast_ma.shift(1) <= slow_ma.shift(1)) & (fast_ma > slow_ma)
    # Death Cross: fast crosses below slow
    death = (fast_ma.shift(1) >= slow_ma.shift(1)) & (fast_ma < slow_ma)

    df.loc[golden, "signal"] = 1
    df.loc[death, "signal"] = -1

    return df


def strategy_rsi_mean_reversion(df: pd.DataFrame, oversold: float, overbought: float) -> pd.DataFrame:
    """RSI Mean Reversion: buy when oversold, sell when overbought."""
    df = df.copy()
    df["signal"] = 0
    df.loc[df["rsi"] < oversold, "signal"] = 1
    df.loc[df["rsi"] > overbought, "signal"] = -1
    return df


def strategy_rsi_divergence(df: pd.DataFrame) -> pd.DataFrame:
    """RSI Divergence: buy on bullish div, sell on bearish div."""
    df = df.copy()
    df["signal"] = 0

    for i in range(20, len(df)):
        window_close = df["close"].iloc[i-10:i+1]
        window_rsi = df["rsi"].iloc[i-10:i+1]

        if (window_close.iloc[-1] < window_close.min() and
            window_rsi.iloc[-1] > window_rsi.min()):
            df.iloc[i, df.columns.get_loc("signal")] = 1

        elif (window_close.iloc[-1] > window_close.max() and
              window_rsi.iloc[-1] < window_rsi.max()):
            df.iloc[i, df.columns.get_loc("signal")] = -1

    return df


def strategy_bollinger_bounce(df: pd.DataFrame) -> pd.DataFrame:
    """Bollinger Band Bounce: buy at lower band, sell at upper band."""
    df = df.copy()
    df["signal"] = 0
    df.loc[df["close"] <= df["bb_lower"], "signal"] = 1
    df.loc[df["close"] >= df["bb_upper"], "signal"] = -1
    return df


def strategy_breakout(df: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Breakout: buy when price breaks N-bar high, sell when breaks N-bar low."""
    df = df.copy()
    df["signal"] = 0

    high_n = df["high"].rolling(lookback).max().shift(1)
    low_n = df["low"].rolling(lookback).min().shift(1)

    df.loc[df["close"] > high_n, "signal"] = 1
    df.loc[df["close"] < low_n, "signal"] = -1

    return df


def strategy_volume_spike(df: pd.DataFrame, vol_mult: float) -> pd.DataFrame:
    """Volume Spike: trade in direction of volume spike."""
    df = df.copy()
    df["signal"] = 0

    spike = df["rvol"] >= vol_mult
    bull_spike = spike & (df["close"] > df["open"])
    bear_spike = spike & (df["close"] < df["open"])

    df.loc[bull_spike, "signal"] = 1
    df.loc[bear_spike, "signal"] = -1
    return df


def strategy_session_entry(df: pd.DataFrame, session_start: int, session_end: int) -> pd.DataFrame:
    """Session Entry: enter at session open."""
    df = df.copy()
    df["signal"] = 0

    in_session = (df["hour"] >= session_start) & (df["hour"] < session_end)
    df.loc[in_session, "signal"] = 1
    return df


def strategy_ema_alignment(df: pd.DataFrame) -> pd.DataFrame:
    """EMA Alignment: buy when all EMAs aligned bullish, sell when all bearish."""
    df = df.copy()
    df["signal"] = 0

    bullish = (df["ema_9"] > df["ema_21"]) & (df["ema_21"] > df["ema_50"]) & (df["close"] > df["ema_200"])
    bearish = (df["ema_9"] < df["ema_21"]) & (df["ema_21"] < df["ema_50"]) & (df["close"] < df["ema_200"])

    df.loc[bullish, "signal"] = 1
    df.loc[bearish, "signal"] = -1
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Backtesting Engine
# ──────────────────────────────────────────────────────────────────────────────

def backtest_strategy(df: pd.DataFrame, signal_col: str = "signal",
                      rr_ratio: float = 1.5, max_hold: int = 24) -> dict:
    """Backtest a signal column with ATR-based SL/TP."""
    trades = []
    balance = 10000.0
    initial = balance
    risk_pct = 1.0

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
            sl = entry - sl_distance
            tp = entry + tp_distance
        else:
            sl = entry + sl_distance
            tp = entry - tp_distance

        result = "open"
        for j in range(i + 2, min(i + 2 + max_hold, len(df))):
            candle = df.iloc[j]
            if direction == "buy":
                if candle["low"] <= sl:
                    result = "loss"
                    break
                if candle["high"] >= tp:
                    result = "win"
                    break
            else:
                if candle["high"] >= sl:
                    result = "loss"
                    break
                if candle["low"] <= tp:
                    result = "win"
                    break

        if result == "win":
            balance += balance * (risk_pct / 100) * rr_ratio
            trades.append({"result": "win", "rr": rr_ratio})
        elif result == "loss":
            balance -= balance * (risk_pct / 100)
            trades.append({"result": "loss", "rr": -1.0})

        balance = max(balance, 0)
        i += 1

    if not trades:
        return {"trades": 0, "win_rate": 0, "profit_factor": 0,
                "total_return": 0, "max_drawdown": 0, "sharpe": 0}

    wins = [t for t in trades if t["result"] == "win"]
    losses = [t for t in trades if t["result"] == "loss"]
    win_rate = len(wins) / len(trades) * 100

    gross_profit = sum(t["rr"] for t in wins) * (initial * risk_pct / 100)
    gross_loss = len(losses) * (initial * risk_pct / 100)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    total_return = (balance - initial) / initial * 100

    equity = [initial]
    for t in trades:
        if t["result"] == "win":
            equity.append(equity[-1] * (1 + risk_pct / 100 * t["rr"]))
        else:
            equity.append(equity[-1] * (1 - risk_pct / 100))

    peak = equity[0]
    max_dd = 0
    for eq in equity:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd

    returns = [t["rr"] * risk_pct / 100 if t["result"] == "win" else -risk_pct / 100 for t in trades]
    sharpe = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0

    return {
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "total_return": round(total_return, 2),
        "max_drawdown": round(max_dd, 2),
        "sharpe": round(sharpe, 3),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Strategy Definitions
# ──────────────────────────────────────────────────────────────────────────────

STRATEGIES = [
    ("ma_9_21", lambda df: strategy_ma_crossover(df, 9, 21), "MA 9/21"),
    ("ma_21_50", lambda df: strategy_ma_crossover(df, 21, 50), "MA 21/50"),
    ("ma_50_200", lambda df: strategy_ma_crossover(df, 50, 200), "MA 50/200"),
    ("rsi_30_70", lambda df: strategy_rsi_mean_reversion(df, 30, 70), "RSI 30/70"),
    ("rsi_25_75", lambda df: strategy_rsi_mean_reversion(df, 25, 75), "RSI 25/75"),
    ("rsi_20_80", lambda df: strategy_rsi_mean_reversion(df, 20, 80), "RSI 20/80"),
    ("rsi_divergence", strategy_rsi_divergence, "RSI Divergence"),
    ("bollinger_bounce", strategy_bollinger_bounce, "Bollinger Bounce"),
    ("breakout_10", lambda df: strategy_breakout(df, 10), "Breakout 10"),
    ("breakout_20", lambda df: strategy_breakout(df, 20), "Breakout 20"),
    ("breakout_50", lambda df: strategy_breakout(df, 50), "Breakout 50"),
    ("vol_1.5x", lambda df: strategy_volume_spike(df, 1.5), "Vol 1.5x"),
    ("vol_2x", lambda df: strategy_volume_spike(df, 2.0), "Vol 2x"),
    ("london_session", lambda df: strategy_session_entry(df, 7, 12), "London"),
    ("ny_session", lambda df: strategy_session_entry(df, 12, 21), "NY"),
    ("overlap_session", lambda df: strategy_session_entry(df, 12, 16), "Overlap"),
    ("ema_alignment", strategy_ema_alignment, "EMA Align"),
]


def main():
    print("=" * 80)
    print("Strategy Tester — Multi-Timeframe")
    print("=" * 80)

    all_results = []

    for tf in TIMEFRAMES:
        print(f"\n{'='*80}")
        print(f"  TIMEFRAME: {tf}")
        print(f"{'='*80}")

        for symbol in SYMBOLS:
            df = load_data(symbol, tf)
            if df.empty or len(df) < 200:
                print(f"\n  Skipping {symbol} [{tf}] — insufficient data")
                continue

            print(f"\n  {symbol} [{tf}] ({len(df)} candles)")

            for strat_id, strat_func, strat_name in STRATEGIES:
                try:
                    df_strat = strat_func(df.copy())
                    stats = backtest_strategy(df_strat)

                    stats["symbol"] = symbol
                    stats["timeframe"] = tf
                    stats["strategy"] = strat_id
                    stats["strategy_name"] = strat_name
                    all_results.append(stats)

                    marker = ""
                    if stats["win_rate"] >= 55 and stats["sharpe"] > 0.3:
                        marker = " *** GOOD ***"
                    elif stats["win_rate"] >= 50:
                        marker = " * OK *"

                    print(f"    {strat_name:<20} trades={stats['trades']:>4}  "
                          f"WR={stats['win_rate']:>5.1f}%  "
                          f"PF={stats['profit_factor']:>5.2f}  "
                          f"Sharpe={stats['sharpe']:>6.3f}  "
                          f"Return={stats['total_return']:>7.2f}%{marker}")

                except Exception as e:
                    print(f"    {strat_name:<20} ERROR: {e}")

    # Sort by Sharpe
    all_results.sort(key=lambda x: x.get("sharpe", 0), reverse=True)

    # Save results
    results_df = pd.DataFrame(all_results)
    csv_path = os.path.join(REPORT_DIR, "strategy_results_mtf.csv")
    results_df.to_csv(csv_path, index=False)

    # Print top 15
    print(f"\n{'='*80}")
    print("  TOP 15 STRATEGIES BY SHARPE RATIO")
    print(f"{'='*80}")
    for i, r in enumerate(all_results[:15], 1):
        print(f"  {i:>2}. {r['symbol']:<8} {r['timeframe']:<5} {r['strategy_name']:<20} "
              f"WR={r['win_rate']}%  PF={r['profit_factor']}  "
              f"Sharpe={r['sharpe']}  Return={r['total_return']}%")

    # Best per symbol
    print(f"\n{'='*80}")
    print("  BEST STRATEGY PER SYMBOL (by Sharpe)")
    print(f"{'='*80}")
    for sym in SYMBOLS:
        sym_results = [r for r in all_results if r["symbol"] == sym]
        if sym_results:
            best = sym_results[0]
            print(f"  {sym:<8} {best['timeframe']:<5} {best['strategy_name']:<20} "
                  f"WR={best['win_rate']}%  PF={best['profit_factor']}  "
                  f"Sharpe={best['sharpe']}  Return={best['total_return']}%")

    print(f"\nFull results saved to {csv_path}")


if __name__ == "__main__":
    main()
