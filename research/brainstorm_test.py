"""
Brainstorm Test — 5 Fresh Ideas (optimized vectorized version)
Tests each strategy across all 8 pairs on 1h data.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PAIRS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "AUDUSD", "NZDUSD", "USDCAD"]
SPREADS = {"EURUSD":1.2,"GBPUSD":1.5,"USDJPY":1.3,"XAUUSD":3.5,"AUDUSD":1.4,"NZDUSD":1.8,"USDCAD":1.3,"GBPJPY":2.5}
PIP_SIZES = {"EURUSD":0.0001,"GBPUSD":0.0001,"USDJPY":0.01,"XAUUSD":0.01,"AUDUSD":0.0001,"NZDUSD":0.0001,"USDCAD":0.0001,"GBPJPY":0.01}

def load_data(symbol, tf="1h"):
    path = os.path.join(DATA_DIR, f"{symbol}_{tf}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, index_col=0, parse_dates=True)

def backtest(df, signal_col, symbol, rr=1.5, max_hold=24):
    trades, balance, initial = [], 10000.0, 10000.0
    risk_pct = 1.0
    i = 0
    while i < len(df) - 1:
        sig = signal_col.iloc[i]
        if sig == 0:
            i += 1
            continue
        entry = df["open"].iloc[i + 1]
        direction = "buy" if sig == 1 else "sell"
        atr = df["atr"].iloc[i] if not pd.isna(df["atr"].iloc[i]) else entry * 0.005
        sl_dist = atr * 1.5
        tp_dist = sl_dist * rr
        if direction == "buy":
            sl, tp = entry - sl_dist, entry + tp_dist
        else:
            sl, tp = entry + sl_dist, entry - tp_dist
        result = "open"
        for j in range(i + 2, min(i + 2 + max_hold, len(df))):
            c = df.iloc[j]
            if direction == "buy":
                if c["low"] <= sl: result = "loss"; break
                if c["high"] >= tp: result = "win"; break
            else:
                if c["high"] >= sl: result = "loss"; break
                if c["low"] <= tp: result = "win"; break
        if result == "win":
            balance += balance * (risk_pct / 100) * rr
        elif result == "loss":
            balance -= balance * (risk_pct / 100)
        balance = max(balance, 0)
        trades.append({"result": result, "rr": rr if result == "win" else -1.0})
        i += 1
    if not trades:
        return {"trades": 0, "win_rate": 0, "profit_factor": 0, "total_return": 0, "max_drawdown": 0, "sharpe": 0}
    wins = [t for t in trades if t["result"] == "win"]
    losses = [t for t in trades if t["result"] == "loss"]
    wr = len(wins) / len(trades) * 100
    gp = sum(t["rr"] for t in wins) * (initial * risk_pct / 100)
    gl = len(losses) * (initial * risk_pct / 100)
    pf = gp / gl if gl > 0 else float("inf")
    tr = (balance - initial) / initial * 100
    eq = [initial]
    for t in trades:
        eq.append(eq[-1] * (1 + risk_pct / 100 * t["rr"]))
    peak = eq[0]; mdd = 0
    for val in eq:
        if val > peak: peak = val
        dd = (peak - val) / peak * 100
        if dd > mdd: mdd = dd
    rets = [t["rr"] * risk_pct / 100 if t["result"] == "win" else -risk_pct / 100 for t in trades]
    sharpe = np.mean(rets) / np.std(rets) if np.std(rets) > 0 else 0
    return {"trades": len(trades), "win_rate": round(wr, 1), "profit_factor": round(pf, 2),
            "total_return": round(tr, 2), "max_drawdown": round(mdd, 2), "sharpe": round(sharpe, 3)}

# ── Strategy 1: 9EMA + RSI Confirmation ──────────────────────────────────
def strat_ema_rsi(df):
    cond_buy = (df["close"] > df["ema_9"]) & (df["rsi"] > 50)
    cond_sell = (df["close"] < df["ema_9"]) & (df["rsi"] < 50)
    s = pd.Series(0, index=df.index)
    s[cond_buy & ~cond_buy.shift(1).fillna(False)] = 1
    s[cond_sell & ~cond_sell.shift(1).fillna(False)] = -1
    return s

# ── Strategy 2: Bollinger Walk ────────────────────────────────────────────
def strat_bb_walk(df):
    s = pd.Series(0, index=df.index)
    bear_streak = np.zeros(len(df), dtype=int)
    bull_streak = np.zeros(len(df), dtype=int)
    bb_bear = (df["close"] >= df["bb_upper"]).values
    bb_bull = (df["close"] <= df["bb_lower"]).values
    for i in range(len(df)):
        if bb_bear[i]:
            bear_streak[i] = bear_streak[i-1] + 1 if i > 0 else 1
        if bb_bull[i]:
            bull_streak[i] = bull_streak[i-1] + 1 if i > 0 else 1
        if bull_streak[i] >= 3:
            s.iloc[i] = 1
        elif bear_streak[i] >= 3:
            s.iloc[i] = -1
    return s

# ── Strategy 3: Volume Disconnect ─────────────────────────────────────────
def strat_vol_disconnect(df):
    s = pd.Series(0, index=df.index)
    body = (df["close"] - df["open"]).abs()
    rng = df["high"] - df["low"]
    body_pct = body / rng.replace(0, np.nan)
    cond = (df["rvol"] >= 2.0) & (body_pct < 0.3)
    s[cond & (df["return_1h"] > 0)] = 1
    s[cond & (df["return_1h"] < 0)] = -1
    return s

# ── Strategy 4: False Breakout Trap (fully vectorized) ────────────────────
def strat_false_breakout(df, lookback=10):
    s = pd.Series(0, index=df.index)
    roll_h = df["high"].rolling(lookback, min_periods=lookback).max().shift(1)
    roll_l = df["low"].rolling(lookback, min_periods=lookback).min().shift(1)
    broke_high = df["high"] > roll_h
    close_below = df["close"].shift(-2) < roll_h
    s[broke_high & close_below] = -1
    broke_low = df["low"] < roll_l
    close_above = df["close"].shift(-2) > roll_l
    s[broke_low & close_above] = 1
    return s

# ── Strategy 5: V-Shape Rule ──────────────────────────────────────────────
def strat_vshape(df):
    s = pd.Series(0, index=df.index)
    rets = df["return_1h"].values
    closes = df["close"].values
    atrs = df["atr"].values
    streak = 0; cum_move = 0.0
    for i in range(1, len(rets)):
        if pd.isna(rets[i]): continue
        if (rets[i] > 0 and streak >= 0) or (rets[i] < 0 and streak <= 0):
            streak += 1 if rets[i] > 0 else -1
            cum_move += abs(rets[i]) * closes[i-1]
        else:
            streak = 1 if rets[i] > 0 else -1
            cum_move = abs(rets[i]) * closes[i-1]
        if abs(streak) >= 3 and cum_move > atrs[i] * 1.5:
            s.iloc[i] = -1 if streak > 0 else 1
            streak = 0; cum_move = 0.0
    return s

STRATEGIES = [
    ("ema_rsi", strat_ema_rsi, "9EMA+RSI"),
    ("bb_walk", strat_bb_walk, "BB Walk"),
    ("vol_disc", strat_vol_disconnect, "Vol Disconnect"),
    ("false_bo", strat_false_breakout, "False Breakout"),
    ("vshape", strat_vshape, "V-Shape"),
]

def main():
    print("=" * 80)
    print(" BRAINSTORM TEST — 5 Fresh Strategies")
    print("=" * 80)
    all_results = []
    for symbol in PAIRS:
        df = load_data(symbol, "1h")
        if df.empty or len(df) < 500:
            print(f"  {symbol}: no data"); continue
        print(f"\n  {symbol} ({len(df)} candles)")
        for sid, sfunc, sname in STRATEGIES:
            try:
                sig = sfunc(df)
                stats = backtest(df, sig, symbol)
                stats["symbol"] = symbol
                stats["strategy"] = sid
                stats["strategy_name"] = sname
                all_results.append(stats)
                marker = ""
                if stats["profit_factor"] >= 1.2 and stats["sharpe"] > 0.3:
                    marker = " ***"
                elif stats["profit_factor"] >= 1.0:
                    marker = " *"
                print(f"    {sname:<18} trades={stats['trades']:>4}  "
                      f"WR={stats['win_rate']:>5.1f}%  PF={stats['profit_factor']:>5.2f}  "
                      f"Sharpe={stats['sharpe']:>6.3f}  DD={stats['max_drawdown']:>5.1f}%{marker}")
            except Exception as e:
                print(f"    {sname:<18} ERROR: {e}")
    ranked = sorted(all_results, key=lambda r: r["profit_factor"], reverse=True)
    print(f"\n{'=' * 80}")
    print(" ALL RESULTS RANKED BY PROFIT FACTOR")
    print("=" * 80)
    for i, r in enumerate(ranked[:20], 1):
        print(f"  {i:>2}. {r['symbol']:<8} {r['strategy_name']:<16} "
              f"trades={r['trades']:>4}  PF={r['profit_factor']:>6.2f}  "
              f"WR={r['win_rate']:>5.1f}%  Sharpe={r['sharpe']:>5.3f}  DD={r['max_drawdown']:>5.1f}%")
    print(f"\n{'=' * 80}")
    print(" BEST PAIR PER STRATEGY")
    print("=" * 80)
    for sid, _, sname in STRATEGIES:
        matches = [r for r in all_results if r["strategy"] == sid]
        if matches:
            best = max(matches, key=lambda r: r["profit_factor"])
            print(f"  {sname:<16} best={best['symbol']:<8} PF={best['profit_factor']:>6.2f}  "
                  f"WR={best['win_rate']:>5.1f}%  Sharpe={best['sharpe']:>5.3f}  "
                  f"trades={best['trades']:>4}")
    # Summary: how many pass PF > 1.0
    passing = sum(1 for r in all_results if r["profit_factor"] >= 1.1 and r["trades"] >= 30)
    total_strat = len([r for r in all_results if r["trades"] >= 10])
    print(f"\n  Passing (PF>=1.1, trades>=30): {passing}/{total_strat}")
    print("\nDone.")

if __name__ == "__main__":
    main()
