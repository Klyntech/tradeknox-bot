"""
Fast Pipeline Backtester — Vectorized Signal Generation
Pre-computes all signals, then simulates trades. Much faster than bar-by-bar.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from config import CONFIG
from strategies import get_pair_config

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Spread + slippage per symbol
COSTS = {
    "XAUUSD": {"spread": 0.50, "slippage": 0.25},
    "EURUSD": {"spread": 0.00015, "slippage": 0.00005},
    "GBPUSD": {"spread": 0.00020, "slippage": 0.00005},
    "USDJPY": {"spread": 0.020, "slippage": 0.005},
    "GBPJPY": {"spread": 0.030, "slippage": 0.005},
    "AUDUSD": {"spread": 0.00015, "slippage": 0.00005},
    "NZDUSD": {"spread": 0.00018, "slippage": 0.00005},
    "USDCAD": {"spread": 0.00018, "slippage": 0.00005},
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_data(symbol: str, timeframe: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{symbol}_{timeframe}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, index_col=0, parse_dates=True)


def compute_structure_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pre-compute market structure signals using vectorized operations.
    Trend, premium/discount, swing points.
    """
    df = df.copy()

    # Trend via EMA alignment
    df["trend_bull"] = (df["ema_21"] > df["ema_50"]) & (df["close"] > df["ema_200"])
    df["trend_bear"] = (df["ema_21"] < df["ema_50"]) & (df["close"] < df["ema_200"])

    # Swing points (20-bar)
    df["swing_high"] = df["high"].rolling(20, center=True).max()
    df["swing_low"] = df["low"].rolling(20, center=True).min()

    # Premium/discount zones
    df["mid_price"] = (df["swing_high"] + df["swing_low"]) / 2
    df["premium"] = df["close"] > df["mid_price"]
    df["discount"] = df["close"] < df["mid_price"]

    # BOS detection (simplified: close > previous swing high = bullish BOS)
    df["bos_bull"] = df["close"] > df["swing_high"].shift(1)
    df["bos_bear"] = df["close"] < df["swing_low"].shift(1)

    # CHoCH (trend reversal signal)
    df["choch_bull"] = df["trend_bull"] & ~df["trend_bull"].shift(1).fillna(False)
    df["choch_bear"] = df["trend_bear"] & ~df["trend_bear"].shift(1).fillna(False)

    # Entry zone: OB/FVG presence (simplified: ATR-based zones)
    df["atr"] = df["atr"] if "atr" in df.columns else df["close"].rolling(14).apply(
        lambda x: np.max(np.abs(np.diff(x))), raw=True
    )

    # Bullish entry: price near swing low + ATR buffer
    df["entry_bull"] = df["close"] <= df["swing_low"] + df["atr"] * 0.5
    # Bearish entry: price near swing high - ATR buffer
    df["entry_bear"] = df["close"] >= df["swing_high"] - df["atr"] * 0.5

    # Candle confirmation (engulfing)
    df["bull_engulf"] = (df["close"] > df["open"]) & (df["close"].shift(1) < df["open"].shift(1)) & \
                        (df["close"] > df["open"].shift(1)) & (df["open"] < df["close"].shift(1))
    df["bear_engulf"] = (df["close"] < df["open"]) & (df["close"].shift(1) > df["open"].shift(1)) & \
                        (df["close"] < df["open"].shift(1)) & (df["open"] > df["close"].shift(1))

    return df


def compute_indicator_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute indicator signals."""
    df = df.copy()

    # RSI signals
    df["rsi_oversold"] = df["rsi"] < 30
    df["rsi_overbought"] = df["rsi"] > 70

    # EMA bias
    df["ema_bull"] = df["ema_21"] > df["ema_50"]
    df["ema_bear"] = df["ema_21"] < df["ema_50"]

    # Volume spike
    df["vol_spike"] = df["rvol"] > 1.5

    return df


def compute_strategy_signals(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Day/session filter only. Add new strategies here in the lab."""
    df = df.copy()
    pair_cfg = get_pair_config(symbol)

    # Day filter
    df["day_name"] = df.index.day_name()
    df["best_day"] = df["day_name"].isin(pair_cfg.get("best_days", []))
    df["avoid_day"] = df["day_name"].isin(pair_cfg.get("avoid_days", []))

    # Session
    df["hour"] = df.index.hour
    sessions = CONFIG.SESSIONS
    df["session"] = "dead_zone"
    df.loc[(df["hour"] >= sessions["overlap"]["start"]) & (df["hour"] < sessions["overlap"]["end"]), "session"] = "overlap"
    df.loc[(df["hour"] >= sessions["london"]["start"]) & (df["hour"] < sessions["london"]["end"]), "session"] = "london"
    df.loc[(df["hour"] >= sessions["new_york"]["start"]) & (df["hour"] < sessions["new_york"]["end"]), "session"] = "new_york"
    df["allowed_session"] = df["session"].isin(CONFIG.ALLOWED_SESSIONS)

    return df
    df["strat_score_bull"] = (df["strat_score_bull"] / max_weight * 3).round().clip(0, 3)
    df["strat_score_bear"] = (df["strat_score_bear"] / max_weight * 3).round().clip(0, 3)

    # Day filter: boost on best days, zero on avoid days
    df.loc[df["best_day"], "strat_score_bull"] = (df.loc[df["best_day"], "strat_score_bull"] + 1).clip(0, 3)
    df.loc[df["best_day"], "strat_score_bear"] = (df.loc[df["best_day"], "strat_score_bear"] + 1).clip(0, 3)
    df.loc[df["avoid_day"], "strat_score_bull"] = 0
    df.loc[df["avoid_day"], "strat_score_bear"] = 0

    return df


def compute_composite_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute composite signal score (0-20) matching the scoring engine weights.
    """
    df = df.copy()

    # Market structure (max 5)
    df["ms_score"] = 0
    df.loc[df["trend_bull"], "ms_score"] += 2
    df.loc[df["trend_bear"], "ms_score"] += 2
    df.loc[df["bos_bull"], "ms_score"] += 2
    df.loc[df["bos_bear"], "ms_score"] += 2
    df.loc[df["choch_bull"], "ms_score"] += 1
    df.loc[df["choch_bear"], "ms_score"] += 1
    df["ms_score"] = df["ms_score"].clip(0, 5)

    # Entry zone (max 4)
    df["ez_score"] = 0
    df.loc[df["entry_bull"], "ez_score"] += 2
    df.loc[df["entry_bear"], "ez_score"] += 2
    df.loc[df["bull_engulf"], "ez_score"] += 1
    df.loc[df["bear_engulf"], "ez_score"] += 1
    df["ez_score"] = df["ez_score"].clip(0, 4)

    # Indicators (max 3)
    df["ind_score"] = 0
    df.loc[df["ema_bull"], "ind_score"] += 1
    df.loc[df["ema_bear"], "ind_score"] += 1
    df.loc[df["vol_spike"], "ind_score"] += 1
    df["ind_score"] = df["ind_score"].clip(0, 3)
    # Strategy confluence (max 3) — 0 (indicator strategies removed, SMC only)

    # Session timing (max 3)
    session_scores = {"overlap": 3, "london": 2, "new_york": 2, "asia": 1, "dead_zone": 0}
    df["sess_score"] = df["session"].map(session_scores).fillna(0).astype(int)

    # News clear (max 2) — always clear in backtest
    df["news_score"] = 2

    # Total buy/sell scores
    df["total_buy"] = df["ms_score"] + df["ez_score"] + df["ind_score"] + df["sess_score"] + df["news_score"]
    df["total_sell"] = df["ms_score"] + df["ez_score"] + df["ind_score"] + df["sess_score"] + df["news_score"]

    return df


def simulate_trades(df: pd.DataFrame, symbol: str,
                    initial_balance: float = 10000.0,
                    risk_pct: float = 1.0,
                    min_score: int = 11,
                    max_hold: int = 48) -> dict:
    """
    Simulate trades on pre-computed signals.
    """
    costs = COSTS.get(symbol, {"spread": 0.00010, "slippage": 0.00005})
    n = len(df)
    trades = []
    balance = initial_balance
    equity = [balance]
    open_trade = None

    for i in range(200, n):
        candle = df.iloc[i]

        # Manage open trade
        if open_trade is not None:
            direction = open_trade["direction"]
            entry = open_trade["entry_with_cost"]
            sl = open_trade["sl"]
            tp1 = open_trade["tp1"]
            tp2 = open_trade["tp2"]
            tp3 = open_trade["tp3"]
            bars_held = i - open_trade["open_bar"]

            result = None
            if direction == "buy":
                if candle["low"] <= sl:
                    result = "loss"
                    pnl = -risk_pct / 100 * balance
                elif candle["high"] >= tp3:
                    result = "win_tp3"
                    pnl = risk_pct / 100 * balance * 3.0
                elif candle["high"] >= tp2:
                    result = "win_tp2"
                    pnl = risk_pct / 100 * balance * 2.0
                elif candle["high"] >= tp1:
                    result = "win_tp1"
                    pnl = risk_pct / 100 * balance * 1.0
                elif bars_held >= max_hold:
                    # Exit at current close
                    exit_price = candle["close"]
                    pnl_pct = (exit_price - entry) / entry * 100
                    result = "exit"
                    pnl = balance * risk_pct / 100 * pnl_pct / 100
            else:
                if candle["high"] >= sl:
                    result = "loss"
                    pnl = -risk_pct / 100 * balance
                elif candle["low"] <= tp3:
                    result = "win_tp3"
                    pnl = risk_pct / 100 * balance * 3.0
                elif candle["low"] <= tp2:
                    result = "win_tp2"
                    pnl = risk_pct / 100 * balance * 2.0
                elif candle["low"] <= tp1:
                    result = "win_tp1"
                    pnl = risk_pct / 100 * balance * 1.0
                elif bars_held >= max_hold:
                    exit_price = candle["close"]
                    pnl_pct = (entry - exit_price) / entry * 100
                    result = "exit"
                    pnl = balance * risk_pct / 100 * pnl_pct / 100

            if result:
                balance += pnl
                balance = max(balance, 0)
                equity.append(balance)
                trades.append({
                    **open_trade,
                    "result": result,
                    "pnl": round(pnl, 2),
                    "close_bar": i,
                    "hold_bars": bars_held,
                })
                open_trade = None
            continue

        # Look for signal
        atr = candle["atr"]
        price = candle["close"]
        day = candle["day_name"]
        session = candle["session"]
        allowed = candle["allowed_session"]
        avoid = candle["avoid_day"]

        if avoid or not allowed:
            continue

        # Buy signal
        if candle["total_buy"] >= min_score:
            sl_dist = atr * 1.5
            entry_with_cost = price + costs["spread"] + costs["slippage"]
            open_trade = {
                "symbol": symbol,
                "direction": "buy",
                "entry": price,
                "entry_with_cost": entry_with_cost,
                "sl": entry_with_cost - sl_dist,
                "tp1": entry_with_cost + sl_dist * 1.5,
                "tp2": entry_with_cost + sl_dist * 2.5,
                "tp3": entry_with_cost + sl_dist * 3.5,
                "score": candle["total_buy"],
                "session": session,
                "day": day,
                "open_bar": i,
                "open_time": str(candle.name),
            }
            continue

        # Sell signal
        if candle["total_sell"] >= min_score:
            sl_dist = atr * 1.5
            entry_with_cost = price - costs["spread"] - costs["slippage"]
            open_trade = {
                "symbol": symbol,
                "direction": "sell",
                "entry": price,
                "entry_with_cost": entry_with_cost,
                "sl": entry_with_cost + sl_dist,
                "tp1": entry_with_cost - sl_dist * 1.5,
                "tp2": entry_with_cost - sl_dist * 2.5,
                "tp3": entry_with_cost - sl_dist * 3.5,
                "score": candle["total_sell"],
                "session": session,
                "day": day,
                "open_bar": i,
                "open_time": str(candle.name),
            }

    # Stats
    closed = [t for t in trades if t.get("result")]
    if not closed:
        return {"symbol": symbol, "trades": 0, "stats": {}, "trades_list": [], "equity": equity}

    wins = [t for t in closed if t["result"].startswith("win")]
    losses = [t for t in closed if t["result"] == "loss"]
    exits = [t for t in closed if t["result"] == "exit"]

    win_pnls = [t["pnl"] for t in wins]
    loss_pnls = [t["pnl"] for t in losses]

    gross_profit = sum(win_pnls) if win_pnls else 0
    gross_loss = abs(sum(loss_pnls)) if loss_pnls else 0.01

    # Max drawdown
    peak = initial_balance
    max_dd = 0
    for eq in equity:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd

    stats = {
        "total_trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "exits": len(exits),
        "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else 0,
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0,
        "total_return": round((balance - initial_balance) / initial_balance * 100, 2),
        "max_drawdown": round(max_dd, 2),
        "avg_win": round(np.mean(win_pnls), 2) if win_pnls else 0,
        "avg_loss": round(np.mean(loss_pnls), 2) if loss_pnls else 0,
        "best_trade": round(max(t["pnl"] for t in closed), 2),
        "worst_trade": round(min(t["pnl"] for t in closed), 2),
        "avg_hold": round(np.mean([t["hold_bars"] for t in closed]), 1),
    }

    return {"symbol": symbol, "trades": len(closed), "stats": stats, "trades_list": closed, "equity": equity}


def print_report(result: dict):
    s = result["stats"]
    if not s:
        print(f"  {result['symbol']}: No trades found")
        return

    print(f"\n{'='*65}")
    print(f"  {result['symbol']}")
    print(f"{'='*65}")
    print(f"  Trades:       {s['total_trades']} (W:{s['wins']} L:{s['losses']} E:{s['exits']})")
    print(f"  Win Rate:     {s['win_rate']}%")
    print(f"  Profit Factor:{s['profit_factor']}")
    print(f"  Total Return: ${s['total_return']:+.2f}%")
    print(f"  Max Drawdown: {s['max_drawdown']}%")
    print(f"  Avg Win:      ${s['avg_win']:+.2f}")
    print(f"  Avg Loss:     ${s['avg_loss']:+.2f}")
    print(f"  Best Trade:   ${s['best_trade']:+.2f}")
    print(f"  Worst Trade:  ${s['worst_trade']:+.2f}")
    print(f"  Avg Hold:     {s['avg_hold']} bars")

    # By session
    by_sess = {}
    for t in result["trades_list"]:
        sess = t["session"]
        if sess not in by_sess:
            by_sess[sess] = {"n": 0, "w": 0, "pnl": 0}
        by_sess[sess]["n"] += 1
        by_sess[sess]["pnl"] += t["pnl"]
        if t["result"].startswith("win"):
            by_sess[sess]["w"] += 1
    if by_sess:
        print(f"\n  By Session:")
        for sess, d in sorted(by_sess.items()):
            wr = d["w"] / d["n"] * 100 if d["n"] > 0 else 0
            print(f"    {sess:<12} {d['n']:>3} trades  WR: {wr:>5.1f}%  P&L: ${d['pnl']:>+8.2f}")

    # By day
    by_day = {}
    for t in result["trades_list"]:
        day = t["day"]
        if day not in by_day:
            by_day[day] = {"n": 0, "w": 0, "pnl": 0}
        by_day[day]["n"] += 1
        by_day[day]["pnl"] += t["pnl"]
        if t["result"].startswith("win"):
            by_day[day]["w"] += 1
    if by_day:
        print(f"\n  By Day:")
        for day in DAYS:
            if day in by_day:
                d = by_day[day]
                wr = d["w"] / d["n"] * 100 if d["n"] > 0 else 0
                print(f"    {day:<12} {d['n']:>3} trades  WR: {wr:>5.1f}%  P&L: ${d['pnl']:>+8.2f}")

    print(f"{'='*65}")


def main():
    import time
    print("=" * 65)
    print("  FAST PIPELINE BACKTESTER (Vectorized)")
    print("  Costs: Spread + Slippage | Strategies: Per-pair + Day filters")
    print("=" * 65)

    symbols = CONFIG.SYMBOLS
    timeframe = "1h"
    initial_balance = 10000.0

    all_results = []
    t_start = time.time()

    # Full period backtest
    print("\n--- FULL PERIOD (Jan-Jul 2026) ---")
    for idx, symbol in enumerate(symbols, 1):
        t_sym = time.time()
        print(f"\n[{idx}/{len(symbols)}] {symbol}...")

        df = load_data(symbol, timeframe)
        if df.empty:
            continue

        # Filter to 2026
        df = df[df.index >= pd.Timestamp("2026-01-01", tz="UTC")]
        df = df[df.index <= pd.Timestamp("2026-07-03", tz="UTC")]

        if len(df) < 250:
            print(f"  Skipping — insufficient data")
            continue

        print(f"  {len(df)} bars ({df.index[0].date()} to {df.index[-1].date()})")

        # Pre-compute all signals
        df = compute_structure_signals(df)
        df = compute_indicator_signals(df)
        df = compute_strategy_signals(df, symbol)
        df = compute_composite_signal(df)

        # Simulate trades
        result = simulate_trades(df, symbol, initial_balance)
        all_results.append(result)
        print_report(result)

        elapsed = time.time() - t_sym
        print(f"  Done in {elapsed:.1f}s")

    # Portfolio summary
    total_trades = sum(r["stats"].get("total_trades", 0) for r in all_results if r["stats"])
    total_wins = sum(r["stats"].get("wins", 0) for r in all_results if r["stats"])
    total_pnl = sum(r["stats"].get("total_return", 0) for r in all_results if r["stats"])
    avg_wr = total_wins / total_trades * 100 if total_trades > 0 else 0

    print(f"\n{'='*65}")
    print(f"  PORTFOLIO SUMMARY")
    print(f"{'='*65}")
    print(f"  Total Trades: {total_trades}")
    print(f"  Win Rate:     {avg_wr:.1f}%")
    print(f"  Combined P&L: ${total_pnl:+.2f}%")
    for r in all_results:
        if r["stats"]:
            s = r["stats"]
            print(f"  {r['symbol']:<8} {s['total_trades']:>3} trades  WR: {s['win_rate']:>5.1f}%  "
                  f"PF: {s['profit_factor']:>5.2f}  P&L: ${s['total_return']:>+8.2f}%  DD: {s['max_drawdown']:.1f}%")
    print(f"{'='*65}")

    # Save trade logs
    for r in all_results:
        if r["trades_list"]:
            df_trades = pd.DataFrame(r["trades_list"])
            df_trades.to_csv(os.path.join(DATA_DIR, f"{r['symbol']}_trades.csv"), index=False)

    print(f"\nTotal time: {(time.time() - t_start):.1f}s")


if __name__ == "__main__":
    main()
