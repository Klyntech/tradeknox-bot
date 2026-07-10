"""
Adversarial Validation — False Breakout Trap
Full test suite: year-by-year, walk-forward, spread stress,
Monte Carlo, bootstrap, trade removal, regime analysis.
"""
import os, sys, json, warnings
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SPREADS = {"EURUSD":1.2,"GBPUSD":1.5,"USDJPY":1.3,"XAUUSD":3.5,"AUDUSD":1.4,"NZDUSD":1.8,"USDCAD":1.3,"GBPJPY":2.5}
PIP_SIZES = {"EURUSD":0.0001,"GBPUSD":0.0001,"USDJPY":0.01,"XAUUSD":0.01,"AUDUSD":0.0001,"NZDUSD":0.0001,"USDCAD":0.0001,"GBPJPY":0.01}

@dataclass
class Trade:
    symbol: str
    entry_date: str
    direction: str
    entry_price: float
    sl: float
    tp: float
    exit_price: float
    exit_reason: str
    pnl_r: float
    net_pnl_r: float
    risk: float
    rr: float
    year: int
    params: Dict = field(default_factory=dict)
    regime: str = ""

def load_data(symbol):
    path = DATA_DIR / f"{symbol}_1h.csv"
    if not path.exists(): return None
    return pd.read_csv(path, parse_dates=True, index_col=0)

def generate_signals(df, lookback=10):
    sig = pd.Series(0, index=df.index)
    roll_h = df["high"].rolling(lookback, min_periods=lookback).max().shift(1)
    roll_l = df["low"].rolling(lookback, min_periods=lookback).min().shift(1)
    broke_h = df["high"] > roll_h
    close_below = df["close"].shift(-2) < roll_h
    sig[broke_h & close_below] = -1
    broke_l = df["low"] < roll_l
    close_above = df["close"].shift(-2) > roll_l
    sig[broke_l & close_above] = 1
    return sig

def simulate_trades(df, signal_col, symbol, rr=1.5, max_hold=24):
    trades = []
    min_start = 20
    for i in range(min_start, len(df) - 1):
        sig = signal_col.iloc[i]
        if sig == 0: continue
        ts = df.index[i]
        entry = df["open"].iloc[i + 1]
        direction = "buy" if sig == 1 else "sell"
        atr = df["atr"].iloc[i] if not pd.isna(df["atr"].iloc[i]) else entry * 0.005
        sl_dist = atr * 1.5
        tp_dist = sl_dist * rr
        if direction == "buy":
            sl, tp = entry - sl_dist, entry + tp_dist
        else:
            sl, tp = entry + sl_dist, entry - tp_dist
        risk = abs(entry - sl)
        exit_price = closes_holder[i] if (closes_holder := df["close"].values) is not None else df["close"].iloc[i]
        exit_reason = "CLOSE_EXIT"
        for j in range(i + 2, min(i + 2 + max_hold, len(df))):
            c = df.iloc[j]
            if direction == "buy":
                if c["low"] <= sl: exit_price = sl; exit_reason = "SL"; break
                if c["high"] >= tp: exit_price = tp; exit_reason = "TP"; break
            else:
                if c["high"] >= sl: exit_price = sl; exit_reason = "SL"; break
                if c["low"] <= tp: exit_price = tp; exit_reason = "TP"; break
            exit_price = c["close"]; exit_reason = "TIME_EXIT"
        if direction == "buy": pnl_raw = exit_price - entry
        else: pnl_raw = entry - exit_price
        pnl_r = pnl_raw / risk if risk > 0 else 0
        pip = PIP_SIZES.get(symbol, 0.0001)
        cost = (SPREADS.get(symbol, 1.0) * pip) + (0.5 * pip) + (0.5 * pip)
        net_r = (pnl_raw - cost) / risk if risk > 0 else 0
        trades.append(Trade(
            symbol=symbol,
            entry_date=ts.strftime("%Y-%m-%d"),
            direction=direction,
            entry_price=float(entry),
            sl=float(sl),
            tp=float(tp),
            exit_price=float(exit_price),
            exit_reason=exit_reason,
            pnl_r=round(float(pnl_r), 4),
            net_pnl_r=round(float(net_r), 4),
            risk=float(risk),
            rr=round(abs(tp - entry) / risk, 2),
            year=ts.year,
        ))
    return trades

def compute_stats(trades, key="net_pnl_r"):
    if not trades:
        return {"total_trades":0,"wins":0,"losses":0,"pf":0,"wr":0,"avg_r":0,"mdd_r":0,"sharpe":0,"gross_profit":0,"gross_loss":0}
    pnls = np.array([getattr(t, key) for t in trades])
    wins = pnls[pnls > 0]; losses = pnls[pnls < 0]
    pf = float(np.sum(wins)/abs(np.sum(losses))) if np.sum(losses) != 0 else 0
    wr = len(wins)/len(pnls) if len(pnls) > 0 else 0
    avg_r = float(np.mean(pnls)) if len(pnls) > 0 else 0
    cum = np.cumsum(pnls); peak = np.maximum.accumulate(cum); dd = peak - cum
    mdd = float(np.max(dd)) if len(dd) > 0 else 0
    std = float(np.std(pnls)) if len(pnls) > 1 else 1
    sharpe = float(np.mean(pnls)/std*np.sqrt(52*7*24)) if std > 0 else 0
    return {"total_trades":len(trades),"wins":len(wins),"losses":len(losses),"pf":round(pf,4),"wr":round(wr,4),
            "avg_r":round(avg_r,4),"mdd_r":round(mdd,2),"sharpe":round(sharpe,4),
            "gross_profit":round(float(np.sum(wins)),2),"gross_loss":round(float(abs(np.sum(losses))),2)}

def print_stats(label, s):
    print(f"  {label:30s}: {s['total_trades']:4d} trades | PF {s['pf']:.3f} | WR {s['wr']:.1%} | AvgR {s['avg_r']:+.4f} | MDD {s['mdd_r']:.1f}R | Sharpe {s['sharpe']:.2f}")

def year_by_year(trades):
    by = {}
    for t in trades: by.setdefault(t.year, []).append(t)
    return {yr: compute_stats(tl) for yr, tl in sorted(by.items())}

def walk_forward(trades, n=5):
    if len(trades) < 20: return []
    ts = sorted(trades, key=lambda t: t.entry_date)
    fs = len(ts) // (n + 1); res = []
    for fold in range(n):
        tr = ts[fold*fs:(fold+1)*fs]; te = ts[(fold+1)*fs:min((fold+2)*fs, len(ts))]
        if len(tr) < 5 or len(te) < 5: continue
        trs = compute_stats(tr); tes = compute_stats(te)
        res.append({"fold":fold+1, "train_period":f"{tr[0].entry_date}->{tr[-1].entry_date}","test_period":f"{te[0].entry_date}->{te[-1].entry_date}",
                     "train_trades":len(tr),"test_trades":len(te),"train_pf":trs["pf"],"train_wr":trs["wr"],
                     "test_pf":tes["pf"],"test_wr":tes["wr"],"test_avg_r":tes["avg_r"],
                     "degradation":round(tes["pf"]/trs["pf"],2) if trs["pf"]>0 else 0})
    return res

def spread_stress(trades, symbol, mults=None):
    if mults is None: mults = [1,2,3,5]
    pip = PIP_SIZES.get(symbol, 0.0001); base = SPREADS.get(symbol, 1.0)*pip + 0.5*pip + 0.5*pip
    res = {}
    for m in mults:
        cost = SPREADS.get(symbol, 1.0)*pip*m + 0.5*pip + 0.5*pip; inc = cost - base
        st = []
        for t in trades:
            new = t.pnl_r - (inc/t.risk) if t.risk > 0 else t.pnl_r
            st.append(Trade(**{**t.__dict__, "net_pnl_r":round(new,4)}))
        res[f"spread_{m}x"] = compute_stats(st)
    return res

def monte_carlo(trades, n=10000, bal=1000, risk=1.0):
    pnls = np.array([t.net_pnl_r for t in trades])
    if len(pnls) < 10: return {"error":"Insufficient"}
    finals, dds, ruin = [], [], 0
    for _ in range(n):
        shuf = np.random.permutation(pnls); b = bal; peak = b; mdd = 0
        for r in shuf:
            b += r * b * (risk/100); peak = max(peak, b)
            dd = (peak-b)/peak*100 if peak > 0 else 0; mdd = max(mdd, dd)
            if b <= 0: ruin += 1; break
        finals.append(b); dds.append(mdd)
    return {"n_simulations":n,"prob_ruin":round(ruin/n,6),"mean_final":round(float(np.mean(finals)),2),
            "median_final":round(float(np.median(finals)),2),"p5_final":round(float(np.percentile(finals,5)),2),
            "p95_final":round(float(np.percentile(finals,95)),2),"mean_max_dd":round(float(np.mean(dds)),2),
            "p95_max_dd":round(float(np.percentile(dds,95)),2),"p99_max_dd":round(float(np.percentile(dds,99)),2),
            "profitable_pct":round(sum(1 for b in finals if b>bal)/n*100,1)}

def bootstrap_mc(trades, n=10000):
    pnls = np.array([t.net_pnl_r for t in trades])
    if len(pnls) < 10: return {"error":"Insufficient"}
    pfs, ars, wrs = [], [], []
    for _ in range(n):
        s = np.random.choice(pnls, len(pnls), replace=True)
        w = sum(r for r in s if r > 0); l = abs(sum(r for r in s if r < 0))
        pfs.append(w/l if l > 0 else 10.0); ars.append(float(np.mean(s)))
        wrs.append(float(sum(1 for r in s if r > 0)/len(s)))
    return {"n_simulations":n,"pf_mean":round(float(np.mean(pfs)),4),"pf_median":round(float(np.median(pfs)),4),
            "pf_p5":round(float(np.percentile(pfs,5)),4),"pf_p95":round(float(np.percentile(pfs,95)),4),
            "pf_p1":round(float(np.percentile(pfs,1)),4),"pf_p99":round(float(np.percentile(pfs,99)),4),
            "pf_below_1":round(sum(1 for p in pfs if p<1.0)/n*100,1),
            "avg_r_mean":round(float(np.mean(ars)),4),"avg_r_p5":round(float(np.percentile(ars,5)),4),
            "avg_r_p95":round(float(np.percentile(ars,95)),4)}

def trade_removal(trades, pcts=None):
    if pcts is None: pcts = [0.1,0.2,0.3]
    pnls = np.array([t.net_pnl_r for t in trades])
    winners = [i for i,p in enumerate(pnls) if p > 0]
    res = {"base":compute_stats(trades)}
    for pct in pcts:
        n_rem = max(1, int(len(winners)*pct)); surv = []
        for _ in range(1000):
            rem = set(np.random.choice(winners, n_rem, replace=False))
            r = [p for i,p in enumerate(pnls) if i not in rem]
            w = sum(p for p in r if p > 0); l = abs(sum(p for p in r if p < 0))
            surv.append(w/l if l > 0 else 0)
        res[f"remove_{int(pct*100)}pct"] = {"mean_pf":round(float(np.mean(surv)),4),"median_pf":round(float(np.median(surv)),4),
                                             "pf_below_1":round(sum(1 for p in surv if p<1.0)/len(surv)*100,1),
                                             "p5_pf":round(float(np.percentile(surv,5)),4),"n_removed":n_rem}
    return res

def classify_regime(df, lb=20):
    c, h, l = df["close"].values, df["high"].values, df["low"].values
    atr = df["atr"].values
    ts = np.full(len(c), np.nan)
    for i in range(lb, len(c)):
        if not np.isnan(atr[i]) and atr[i] > 0:
            roc = (c[i]-c[i-lb])/c[i-lb]
            ts[i] = abs(roc)/(atr[i]/c[i])
    vr = np.full(len(c), np.nan)
    for i in range(lb*3, len(c)):
        w = atr[i-lb*3:i]; v = w[~np.isnan(w)]
        if len(v) > 10 and not np.isnan(atr[i]): vr[i] = sum(x < atr[i] for x in v)/len(v)
    reg = pd.Series("UNCLASSIFIED", index=df.index)
    for i in range(lb*3, len(df)):
        tv, vv = np.nan_to_num(ts[i], nan=0), np.nan_to_num(vr[i], nan=0.5)
        prim = "TRENDING" if tv > 1.5 else ("RANGING" if tv < 0.5 else "MIXED")
        vol = "HIGH_VOL" if vv > 0.75 else ("LOW_VOL" if vv < 0.25 else "")
        reg.iloc[i] = vol if vol else prim
    return reg

def regime_analysis(trades, df):
    regs = classify_regime(df); rt = {}
    for t in trades:
        date = pd.Timestamp(t.entry_date, tz="UTC")
        mask = df.index <= date
        if not mask.any(): continue
        r = regs.iloc[mask.sum()-1]
        rt.setdefault(r, []).append(t)
        t.regime = r
    return {r: compute_stats(tl) for r, tl in sorted(rt.items())}

def run_suite(trades, symbol, df, label=""):
    res = {}
    if not trades:
        print(f"  [{label}] No trades"); return res
    res["baseline"] = compute_stats(trades)
    print_stats(f"[{label}] Baseline", res["baseline"])
    print(f"\n  [{label}] Year-by-Year:")
    yby = year_by_year(trades); res["year_by_year"] = yby
    for yr, s in yby.items():
        print(f"    {yr}: {s['total_trades']:4d} trades | PF {s['pf']:.3f} | WR {s['wr']:.1%} | AvgR {s['avg_r']:+.4f}")
    yrs_bad = sum(1 for s in yby.values() if s["pf"] < 0.9 and s["total_trades"] >= 10)
    res["years_pf_below_0.9"] = yrs_bad
    print(f"\n  [{label}] Walk-Forward (5-fold):")
    wf = walk_forward(trades, 5); res["walk_forward"] = wf
    for f in wf:
        print(f"    Fold {f['fold']}: Train PF {f['train_pf']:.3f} -> Test PF {f['test_pf']:.3f} (deg: {f['degradation']:.2f}x)")
    avg_test = np.mean([f["test_pf"] for f in wf]) if wf else 0
    all_pos = all(f["test_pf"] > 1.0 for f in wf) if wf else False
    res["wf_avg_test"] = round(float(avg_test), 4); res["wf_all_pos"] = all_pos
    print(f"\n  [{label}] Spread Stress:")
    stress = spread_stress(trades, symbol); res["spread_stress"] = stress
    for k, s in stress.items():
        print(f"    {k:12s}: PF {s['pf']:.4f} | WR {s['wr']:.1%} | AvgR {s['avg_r']:+.4f}")
    stress_ok = stress.get("spread_3x",{}).get("pf",0) > 1.0
    res["stress_survives_3x"] = stress_ok
    print(f"\n  [{label}] Monte Carlo (10,000):")
    mc = monte_carlo(trades, 10000); res["monte_carlo"] = mc
    if "error" not in mc:
        print(f"    P(Ruin): {mc['prob_ruin']:.4f}")
        print(f"    Mean Final: ${mc['mean_final']:.2f} | Median: ${mc['median_final']:.2f}")
        print(f"    P95 Max DD: {mc['p95_max_dd']:.1f}%")
        print(f"    Profitable: {mc['profitable_pct']:.1f}%")
    mc_ok = mc.get("prob_ruin",1) < 0.05 and mc.get("p95_max_dd",100) < 30
    res["mc_survives"] = mc_ok
    print(f"\n  [{label}] Bootstrap (10,000):")
    bmc = bootstrap_mc(trades, 10000); res["bootstrap"] = bmc
    if "error" not in bmc:
        print(f"    PF Mean: {bmc['pf_mean']:.4f} | Median: {bmc['pf_median']:.4f}")
        print(f"    PF P5-P95: [{bmc['pf_p5']:.4f}, {bmc['pf_p95']:.4f}]")
        print(f"    P(PF<1.0): {bmc['pf_below_1']:.1f}%")
    bmc_ok = bmc.get("pf_p5",0) > 0.9
    res["bmc_survives"] = bmc_ok
    print(f"\n  [{label}] Trade Removal:")
    rem = trade_removal(trades); res["trade_removal"] = rem
    for k, s in rem.items():
        if k == "base": print(f"    Base:     PF {s['pf']:.4f}")
        else: print(f"    {k:20s}: PF {s['mean_pf']:.4f} (P5: {s['p5_pf']:.4f}) | PF<1: {s['pf_below_1']:.1f}%")
    rem_ok = rem.get("remove_10pct",{}).get("pf_below_1",100) < 50
    res["removal_survives_10pct"] = rem_ok
    print(f"\n  [{label}] Regime Analysis:")
    ra = regime_analysis(trades, df); res["regime"] = ra
    for r, s in sorted(ra.items()):
        print(f"    {r:15s}: {s['total_trades']:4d} trades | PF {s['pf']:.3f} | WR {s['wr']:.1%} | AvgR {s['avg_r']:+.4f}")
    return res

def verdict(res):
    score = 0; det = []
    if res.get("baseline",{}).get("pf",0) > 1.2: score += 1; det.append("PF>1.2")
    else: det.append("PF<=1.2")
    if res.get("wf_all_pos",False) and res.get("wf_avg_test",0) > 1.0: score += 1; det.append("WF+")
    else: det.append("WF-")
    if res.get("stress_survives_3x",False): score += 1; det.append("Spread+")
    else: det.append("Spread-")
    if res.get("mc_survives",False): score += 1; det.append("MC+")
    else: det.append("MC-")
    if res.get("bmc_survives",False): score += 1; det.append("Bootstrap+")
    else: det.append("Bootstrap-")
    if res.get("removal_survives_10pct",False): score += 1; det.append("Removal+")
    else: det.append("Removal-")
    if score >= 5: return f"PASS ({score}/6): {', '.join(det)}"
    elif score >= 3: return f"MARGINAL ({score}/6): {', '.join(det)}"
    else: return f"FAIL ({score}/6): {', '.join(det)}"

def main():
    print("=" * 80)
    print("  ADVERSARIAL VALIDATION — False Breakout Trap")
    print("=" * 80)
    symbols = ["GBPUSD", "EURUSD", "NZDUSD", "AUDUSD", "USDJPY"]
    all_data = {}
    for sym in symbols:
        print(f"\n{'#' * 80}")
        print(f"  {sym}")
        print(f"{'#' * 80}")
        df = load_data(sym)
        if df is None or len(df) < 500:
            print(f"  {sym}: no data"); continue
        sig = generate_signals(df)
        trades = simulate_trades(df, sig, sym)
        if not trades:
            print(f"  {sym}: no trades"); continue
        res = run_suite(trades, sym, df, label=sym)
        print(f"\n  >>> VERDICT [{sym}]: {verdict(res)}")
        all_data[sym] = res
    out = OUTPUT_DIR / "adversarial_false_breakout.json"
    with open(out, "w") as f:
        json.dump(all_data, f, indent=2, default=str)
    print(f"\n  Results saved to {out}")
    print("Done.")

if __name__ == "__main__":
    main()
