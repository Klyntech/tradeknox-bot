"""
Optimized Strategy Tester — Faster, fewer trades, meaningful results.
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def load(symbol):
    p = os.path.join(DATA_DIR, f"{symbol}_1h.csv")
    return pd.read_csv(p, index_col=0, parse_dates=True) if os.path.exists(p) else pd.DataFrame()

def backtest(df, signal_col="signal", max_hold=48, risk_pct=1.0, rr=1.5):
    """Efficient backtest — only trades on signal changes."""
    trades = []
    balance = 10000.0
    i = 0
    n = len(df)

    while i < n - 1:
        sig = df[signal_col].iloc[i]
        if sig == 0:
            i += 1
            continue

        entry = df["open"].iloc[i+1]
        direction = int(sig)
        atr = df["atr"].iloc[i] if not pd.isna(df["atr"].iloc[i]) else entry * 0.005

        sl_dist = atr * 1.5
        tp_dist = sl_dist * rr

        if direction == 1:
            sl, tp = entry - sl_dist, entry + tp_dist
        else:
            sl, tp = entry + sl_dist, entry - tp_dist

        result = 0
        for j in range(i+2, min(i+2+max_hold, n)):
            c = df.iloc[j]
            if direction == 1:
                if c["low"] <= sl: result = -1; break
                if c["high"] >= tp: result = 1; break
            else:
                if c["high"] >= sl: result = -1; break
                if c["low"] <= tp: result = 1; break

        if result == 1:
            balance *= (1 + risk_pct/100 * rr)
        elif result == -1:
            balance *= (1 - risk_pct/100)

        trades.append(result)
        i += 1

    if not trades:
        return {"trades": 0, "wr": 0, "pf": 0, "ret": 0, "sharpe": 0}

    wins = sum(1 for t in trades if t == 1)
    losses = sum(1 for t in trades if t == -1)
    wr = wins/len(trades)*100

    gross_p = wins * rr * (risk_pct/100)
    gross_l = losses * (risk_pct/100)
    pf = gross_p / gross_l if gross_l > 0 else 99

    ret = (balance - 10000) / 10000 * 100
    rets = [rr*risk_pct/100 if t==1 else -risk_pct/100 for t in trades]
    sharpe = np.mean(rets)/np.std(rets) if np.std(rets) > 0 else 0

    return {"trades": len(trades), "wins": wins, "losses": losses,
            "wr": round(wr,1), "pf": round(pf,2), "ret": round(ret,2),
            "sharpe": round(sharpe,3)}

def ma_cross(df, f, s):
    d = df.copy()
    d["signal"] = 0
    fast = d[f"ema_{f}"]
    slow = d[f"ema_{s}"]
    # Only signal on crossover, not position
    golden = (fast.shift(1) <= slow.shift(1)) & (fast > slow)  # cross above
    death = (fast.shift(1) >= slow.shift(1)) & (fast < slow)   # cross below
    d.loc[golden, "signal"] = 1
    d.loc[death, "signal"] = -1
    return d

def rsi_mr(df, lo, hi):
    d = df.copy()
    d["signal"] = 0
    d.loc[d["rsi"]<lo, "signal"] = 1
    d.loc[d["rsi"]>hi, "signal"] = -1
    return d

def bollinger(df):
    d = df.copy()
    d["signal"] = 0
    d.loc[d["close"]<=d["bb_lower"], "signal"] = 1
    d.loc[d["close"]>=d["bb_upper"], "signal"] = -1
    return d

def breakout(df, n):
    d = df.copy()
    h = d["high"].rolling(n).max().shift(1)
    l = d["low"].rolling(n).min().shift(1)
    d["signal"] = 0
    d.loc[d["close"]>h, "signal"] = 1
    d.loc[d["close"]<l, "signal"] = -1
    return d

def vol_spike(df, mult):
    d = df.copy()
    d["signal"] = 0
    spike = d["rvol"] >= mult
    d.loc[spike & (d["close"]>d["open"]), "signal"] = 1
    d.loc[spike & (d["close"]<d["open"]), "signal"] = -1
    return d

def ema_align(df):
    d = df.copy()
    d["signal"] = 0
    # Bullish: all EMAs aligned + price above 200 EMA
    bull_aligned = (d["ema_9"]>d["ema_21"]) & (d["ema_21"]>d["ema_50"]) & (d["close"]>d["ema_200"])
    bear_aligned = (d["ema_9"]<d["ema_21"]) & (d["ema_21"]<d["ema_50"]) & (d["close"]<d["ema_200"])
    # Signal on alignment change (was not aligned, now aligned)
    bull_enter = bull_aligned & ~bull_aligned.shift(1).fillna(False)
    bear_enter = bear_aligned & ~bear_aligned.shift(1).fillna(False)
    d.loc[bull_enter, "signal"] = 1
    d.loc[bear_enter, "signal"] = -1
    return d

def rsi_div(df):
    d = df.copy()
    d["signal"] = 0
    for i in range(20, len(d)):
        ec = d["close"].iloc[i-10:i+1]
        er = d["rsi"].iloc[i-10:i+1]
        if ec.iloc[-1]<ec.min() and er.iloc[-1]>er.min():
            d.iloc[i, d.columns.get_loc("signal")] = 1
        elif ec.iloc[-1]>ec.max() and er.iloc[-1]<er.max():
            d.iloc[i, d.columns.get_loc("signal")] = -1
    return d

STRATEGIES = [
    ("MA 9/21", lambda d: ma_cross(d,9,21)),
    ("MA 21/50", lambda d: ma_cross(d,21,50)),
    ("MA 50/200", lambda d: ma_cross(d,50,200)),
    ("RSI 30/70", lambda d: rsi_mr(d,30,70)),
    ("RSI 25/75", lambda d: rsi_mr(d,25,75)),
    ("RSI 20/80", lambda d: rsi_mr(d,20,80)),
    ("RSI Divergence", rsi_div),
    ("Bollinger Bounce", bollinger),
    ("Breakout 20", lambda d: breakout(d,20)),
    ("Volume 1.5x", lambda d: vol_spike(d,1.5)),
    ("EMA Alignment", ema_align),
]

SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY"]

results = []
for sym in SYMBOLS:
    df = load(sym)
    if df.empty: continue
    print(f"\n{sym}:")
    for name, func in STRATEGIES:
        try:
            ds = func(df.copy())
            stats = backtest(ds)
            stats["symbol"] = sym
            stats["strategy"] = name
            results.append(stats)
            tag = " ***" if stats["wr"]>=55 and stats["sharpe"]>0.2 else ""
            print(f"  {name:<20} trades={stats['trades']:>5} WR={stats['wr']:>5.1f}% PF={stats['pf']:>5.2f} Sharpe={stats['sharpe']:>6.3f} Ret={stats['ret']:>8.2f}%{tag}")
        except Exception as e:
            print(f"  {name:<20} ERROR: {e}")

rdf = pd.DataFrame(results)
rdf.to_csv(os.path.join(DATA_DIR, "strategy_results.csv"), index=False)

print("\n" + "="*70)
print("TOP 10 BY SHARPE:")
rdf = rdf.sort_values("sharpe", ascending=False)
for i, r in rdf.head(10).iterrows():
    print(f"  {r['symbol']} {r['strategy']:<20} WR={r['wr']}% PF={r['pf']} Sharpe={r['sharpe']} Ret={r['ret']}%")
