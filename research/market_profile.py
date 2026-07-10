"""
Phase 2: Market Character Profile
Analyzes returns, volatility, session performance, and market regimes.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load_data(symbol: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{symbol}_1h.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df


def classify_session(hour: int) -> str:
    """Classify UTC hour into trading session."""
    if 12 <= hour < 16:
        return "overlap"
    elif 7 <= hour < 12:
        return "london"
    elif 16 <= hour < 21:
        return "new_york"
    elif 0 <= hour < 8:
        return "asia"
    else:
        return "dead_zone"


def classify_regime(df: pd.DataFrame, lookback: int = 50) -> str:
    """Classify market as trending or ranging based on ADX-like measure."""
    if len(df) < lookback:
        return "unknown"

    # Use directional movement
    high = df["high"]
    low = df["low"]
    close = df["close"]

    # Simplified ADX: |close - close[20]| / ATR
    price_move = (close - close.shift(20)).abs()
    atr = df["atr"]
    trend_strength = price_move / atr.replace(0, np.nan)

    current = trend_strength.iloc[-1] if not pd.isna(trend_strength.iloc[-1]) else 0

    if current > 1.5:
        return "trending"
    elif current < 0.5:
        return "ranging"
    else:
        return "transitioning"


def analyze_symbol(symbol: str) -> dict:
    """Full market character analysis for one symbol."""
    df = load_data(symbol)
    if df.empty:
        return {}

    results = {"symbol": symbol}

    # ── Basic Stats ────────────────────────────────────────────────────────
    results["total_candles"] = len(df)
    results["date_range"] = f"{df.index[0].date()} to {df.index[-1].date()}"
    results["avg_daily_range"] = round(df["volatility"].mean(), 4)

    # ── Returns Distribution ───────────────────────────────────────────────
    returns = df["return_1h"].dropna()
    results["avg_return"] = round(returns.mean() * 100, 4)
    results["std_return"] = round(returns.std() * 100, 4)
    results["positive_pct"] = round((returns > 0).sum() / len(returns) * 100, 1)
    results["skew"] = round(returns.skew(), 3)
    results["kurtosis"] = round(returns.kurtosis(), 3)

    # ── Session Analysis ───────────────────────────────────────────────────
    df["session"] = df["hour"].apply(classify_session)
    session_stats = {}

    for session in ["london", "new_york", "overlap", "asia"]:
        sess_df = df[df["session"] == session]
        if len(sess_df) == 0:
            continue

        sess_returns = sess_df["return_1h"].dropna()
        # Trend-following: buy if close > open, sell if close < open
        sess_df_copy = sess_df.copy()
        sess_df_copy["direction"] = np.where(
            sess_df_copy["close"] > sess_df_copy["open"], "buy", "sell"
        )
        # Forward return after signal
        sess_df_copy["fwd_return"] = sess_df_copy["close"].shift(-1) / sess_df_copy["close"] - 1

        # Win rate if trading with candle direction
        correct = (
            ((sess_df_copy["direction"] == "buy") & (sess_df_copy["fwd_return"] > 0)) |
            ((sess_df_copy["direction"] == "sell") & (sess_df_copy["fwd_return"] < 0))
        )
        win_rate = correct.sum() / len(correct) * 100 if len(correct) > 0 else 0

        session_stats[session] = {
            "candles": len(sess_df),
            "avg_return": round(sess_returns.mean() * 100, 4),
            "std_return": round(sess_returns.std() * 100, 4),
            "volatility": round(sess_df["volatility"].mean(), 4),
            "directional_win_rate": round(win_rate, 1),
        }

    results["sessions"] = session_stats

    # ── Hourly Analysis ────────────────────────────────────────────────────
    hourly_returns = df.groupby("hour")["return_1h"].agg(["mean", "std", "count"])
    hourly_returns["mean_pct"] = (hourly_returns["mean"] * 100).round(4)
    hourly_returns["sharpe"] = (hourly_returns["mean"] / hourly_returns["std"]).round(3)

    best_hours = hourly_returns.nlargest(3, "mean_pct")
    worst_hours = hourly_returns.nsmallest(3, "mean_pct")

    results["best_hours"] = [(int(h), round(r, 4)) for h, r in zip(best_hours.index, best_hours["mean_pct"])]
    results["worst_hours"] = [(int(h), round(r, 4)) for h, r in zip(worst_hours.index, worst_hours["mean_pct"])]

    # ── Trending vs Ranging ────────────────────────────────────────────────
    # Rolling 50-bar trend strength
    price_move = (df["close"] - df["close"].shift(50)).abs()
    trend_strength = price_move / df["atr"].replace(0, np.nan)
    trend_strength = trend_strength.dropna()

    trending_pct = (trend_strength > 1.5).sum() / len(trend_strength) * 100
    ranging_pct = (trend_strength < 0.5).sum() / len(trend_strength) * 100
    transition_pct = 100 - trending_pct - ranging_pct

    results["regime_distribution"] = {
        "trending": round(trending_pct, 1),
        "ranging": round(ranging_pct, 1),
        "transitioning": round(transition_pct, 1),
    }

    # ── RSI Distribution ───────────────────────────────────────────────────
    rsi = df["rsi"]
    results["rsi_stats"] = {
        "mean": round(rsi.mean(), 1),
        "std": round(rsi.std(), 1),
        "oversold_pct": round((rsi < 30).sum() / len(rsi) * 100, 1),
        "overbought_pct": round((rsi > 70).sum() / len(rsi) * 100, 1),
    }

    # ── MA Crossover Performance ───────────────────────────────────────────
    for fast, slow in [(9, 21), (21, 50), (50, 200)]:
        col_fast = f"ema_{fast}"
        col_slow = f"ema_{slow}"
        if col_fast not in df.columns or col_slow not in df.columns:
            continue

        df_ma = df.copy()
        df_ma["ma_signal"] = 0
        df_ma.loc[df_ma[col_fast] > df_ma[col_slow], "ma_signal"] = 1  # buy
        df_ma.loc[df_ma[col_fast] < df_ma[col_slow], "ma_signal"] = -1  # sell

        # Forward return aligned with signal
        df_ma["fwd_return"] = df_ma["close"].shift(-1) / df_ma["close"] - 1
        df_ma["strategy_return"] = df_ma["ma_signal"] * df_ma["fwd_return"]

        valid = df_ma["strategy_return"].dropna()
        if len(valid) > 0:
            total_return = valid.sum() * 100
            win_rate = (valid > 0).sum() / len(valid) * 100
            sharpe = valid.mean() / valid.std() if valid.std() > 0 else 0

            results[f"ma_{fast}_{slow}"] = {
                "total_return_pct": round(total_return, 2),
                "win_rate": round(win_rate, 1),
                "sharpe": round(sharpe, 3),
                "trades": len(valid),
            }

    return results


def print_report(results: dict):
    """Print formatted market profile report."""
    sym = results["symbol"]
    print(f"\n{'='*60}")
    print(f"  MARKET PROFILE — {sym}")
    print(f"{'='*60}")
    print(f"  Period: {results.get('date_range', 'N/A')}")
    print(f"  Candles: {results.get('total_candles', 0)}")
    print(f"  Avg Hourly Return: {results.get('avg_return', 0)}%")
    print(f"  Positive Hours: {results.get('positive_pct', 0)}%")
    print(f"  Skew: {results.get('skew', 0)} | Kurtosis: {results.get('kurtosis', 0)}")

    print(f"\n  Sessions:")
    for sess, stats in results.get("sessions", {}).items():
        print(f"    {sess:<12} candles={stats['candles']:>5}  "
              f"avg_ret={stats['avg_return']:>7}%  "
              f"vol={stats['volatility']:>6}%  "
              f"dir_wr={stats['directional_win_rate']}%")

    print(f"\n  Best Hours (UTC): {results.get('best_hours', [])}")
    print(f"  Worst Hours (UTC): {results.get('worst_hours', [])}")

    regime = results.get("regime_distribution", {})
    print(f"\n  Market Regime: trending={regime.get('trending', 0)}%  "
          f"ranging={regime.get('ranging', 0)}%  "
          f"transition={regime.get('transitioning', 0)}%")

    rsi = results.get("rsi_stats", {})
    print(f"\n  RSI: mean={rsi.get('mean', 0)}  "
          f"oversold={rsi.get('oversold_pct', 0)}%  "
          f"overbought={rsi.get('overbought_pct', 0)}%")

    print(f"\n  MA Crossover Performance:")
    for key in ["ma_9_21", "ma_21_50", "ma_50_200"]:
        if key in results:
            ma = results[key]
            print(f"    {key}: return={ma['total_return_pct']}%  "
                  f"WR={ma['win_rate']}%  Sharpe={ma['sharpe']}")

    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("Phase 2: Market Character Profile")
    print("=" * 60)

    symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY"]
    all_results = []

    for sym in symbols:
        results = analyze_symbol(sym)
        if results:
            all_results.append(results)
            print_report(results)

    # Save summary
    report_path = os.path.join(REPORT_DIR, "market_profile.txt")
    with open(report_path, "w") as f:
        for r in all_results:
            f.write(f"{r['symbol']}\n")
            for k, v in r.items():
                if k != "symbol":
                    f.write(f"  {k}: {v}\n")
            f.write("\n")
    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()
