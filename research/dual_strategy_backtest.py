"""
Dual-Strategy Portfolio Backtest
  • False Breakout Trap (counter-trend, ranging)
  • SMC 8-Gate proxy via simplified structure signals (trend-following)
  • Regime-based allocation: FB when ranging, SMC when trending

Tests across all 8 pairs on 1h data.
"""

import sys, warnings, json, traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent.parent))
from false_breakout import backtest_symbol

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

ALL_SYMBOLS = ["XAUUSD", "GBPUSD", "EURUSD", "USDJPY",
               "GBPJPY", "AUDUSD", "NZDUSD", "USDCAD"]

SPREADS = {"EURUSD":1.2,"GBPUSD":1.5,"USDJPY":1.3,"XAUUSD":3.5,"AUDUSD":1.4,"NZDUSD":1.8,"USDCAD":1.3,"GBPJPY":2.5}
PIP_SIZES = {"EURUSD":0.0001,"GBPUSD":0.0001,"USDJPY":0.01,"XAUUSD":0.01,"AUDUSD":0.0001,"NZDUSD":0.0001,"USDCAD":0.0001,"GBPJPY":0.01}


def load_data(symbol: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{symbol}_1h.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=True, index_col=0)


def classify_regime(df: pd.DataFrame, lb: int = 20):
    """Regime classification — same as adversarial test."""
    c, h, l = df["close"].values, df["high"].values, df["low"].values
    atr = df["atr"].values if "atr" in df.columns else np.full(len(c), np.nan)
    ts = np.full(len(c), np.nan)
    for i in range(lb, len(c)):
        if not np.isnan(atr[i]) and atr[i] > 0:
            roc = (c[i] - c[i-lb]) / c[i-lb]
            ts[i] = abs(roc) / (atr[i] / c[i])
    vr = np.full(len(c), np.nan)
    for i in range(lb*3, len(c)):
        w = atr[i-lb*3:i]; v = w[~np.isnan(w)]
        if len(v) > 10 and not np.isnan(atr[i]):
            vr[i] = sum(x < atr[i] for x in v) / len(v)
    reg = pd.Series("UNCLASSIFIED", index=df.index)
    for i in range(lb*3, len(df)):
        tv = np.nan_to_num(ts[i], nan=0)
        vv = np.nan_to_num(vr[i], nan=0.5)
        prim = "TRENDING" if tv > 1.5 else ("RANGING" if tv < 0.5 else "MIXED")
        vol = "HIGH_VOL" if vv > 0.75 else ("LOW_VOL" if vv < 0.25 else "")
        reg.iloc[i] = vol if vol else prim
    return reg


def compute_costs(symbol: str) -> Tuple[float, float]:
    """Return (spread_cost, total_round_trip_cost) in price units."""
    pip = PIP_SIZES.get(symbol, 0.0001)
    spread_cost = SPREADS.get(symbol, 1.0) * pip
    total_cost = spread_cost + 0.5*pip + 0.5*pip  # spread + entry comm + exit comm
    return spread_cost, total_cost


def stats_from_trades(trades: List[Dict], key: str = "pnl_r") -> Dict:
    if not trades:
        return {"total_trades":0,"wins":0,"losses":0,"pf":0,"wr":0,"avg_r":0,"mdd_r":0,"sharpe":0}
    pnls = np.array([t[key] for t in trades])
    wins = pnls[pnls > 0]; losses = pnls[pnls < 0]
    pf = float(np.sum(wins)/abs(np.sum(losses))) if np.sum(losses) != 0 else 0
    wr = len(wins)/len(pnls) if len(pnls) > 0 else 0
    avg_r = float(np.mean(pnls))
    cum = np.cumsum(pnls)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    mdd = float(np.max(dd)) if len(dd) > 0 else 0
    std = float(np.std(pnls)) if len(pnls) > 1 else 1
    sharpe = float(np.mean(pnls)/std*np.sqrt(52*7*24)) if std > 0 else 0
    return {"total_trades":len(trades),"wins":int(len(wins)),"losses":int(len(losses)),
            "pf":round(pf,4),"wr":round(wr,4),"avg_r":round(avg_r,4),"mdd_r":round(mdd,2),"sharpe":round(sharpe,4)}


def simulate_smc_proxy(df: pd.DataFrame, symbol: str, precomputed_regime=None) -> List[Dict]:
    """
    Simplified SMC proxy: trend-following using BOS-like logic.
    Only enters when regime is TRENDING/HIGH_VOL.
    Pre-compute regime series for speed.
    """
    trades: List[Dict] = []
    roll_h = df["high"].rolling(10, min_periods=10).max().shift(1)
    roll_l = df["low"].rolling(10, min_periods=10).min().shift(1)
    _, total_cost = compute_costs(symbol)

    if precomputed_regime is None:
        precomputed_regime = classify_regime(df)
    reg = precomputed_regime.values

    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    opens = df["open"].values
    atrs = df["atr"].values if "atr" in df.columns else np.full(len(df), np.nan)
    rh = roll_h.values
    rl = roll_l.values

    for i in range(25, len(df) - 3):
        r = str(reg[i]) if i < len(reg) else "UNCLASSIFIED"
        if "RANGING" in r or "LOW_VOL" in r or "UNCLASSIFIED" in r:
            continue

        atr = float(atrs[i]) if not np.isnan(atrs[i]) else float(closes[i]) * 0.005
        entry = float(opens[i + 1])
        sl_dist = atr * 1.5
        tp_dist = sl_dist * 1.5

        # Bullish break
        if highs[i] > rh[i] and closes[i] > rh[i]:
            sl = entry - sl_dist
            tp = entry + tp_dist
            pnl = 0.0; reason = "TIME"
            for j in range(i + 2, min(i + 2 + 24, len(df))):
                if lows[j] <= sl: pnl = -1.0; reason = "SL"; break
                if highs[j] >= tp: pnl = 1.5; reason = "TP"; break
                pnl = (closes[j] - entry) / sl_dist
            cost_r = total_cost / sl_dist if sl_dist > 0 else 0
            trades.append({
                "symbol": symbol, "entry_date": str(df.index[i].date()),
                "direction": "buy", "entry": entry, "sl": sl, "tp": tp,
                "pnl_r": round(pnl - cost_r, 4),
                "exit_reason": reason, "regime": r,
            })

        # Bearish break
        if lows[i] < rl[i] and closes[i] < rl[i]:
            sl = entry + sl_dist
            tp = entry - tp_dist
            pnl = 0.0; reason = "TIME"
            for j in range(i + 2, min(i + 2 + 24, len(df))):
                if highs[j] >= sl: pnl = -1.0; reason = "SL"; break
                if lows[j] <= tp: pnl = 1.5; reason = "TP"; break
                pnl = (entry - closes[j]) / sl_dist
            cost_r = total_cost / sl_dist if sl_dist > 0 else 0
            trades.append({
                "symbol": symbol, "entry_date": str(df.index[i].date()),
                "direction": "sell", "entry": entry, "sl": sl, "tp": tp,
                "pnl_r": round(pnl - cost_r, 4),
                "exit_reason": reason, "regime": r,
            })

    return trades


def find_overlaps(fb_trades: List[Dict], smc_trades: List[Dict]) -> Dict:
    """
    Find cases where FB and SMC fire on SAME bar in OPPOSITE directions.
    Returns count and list of such overlaps.
    """
    fb_by_date: Dict[str, List[Dict]] = {}
    for t in fb_trades:
        fb_by_date.setdefault(t["entry_date"], []).append(t)

    smc_by_date: Dict[str, List[Dict]] = {}
    for t in smc_trades:
        smc_by_date.setdefault(t["entry_date"], []).append(t)

    conflicts = []
    common = set(fb_by_date.keys()) & set(smc_by_date.keys())
    for date in common:
        for fb in fb_by_date[date]:
            for smc in smc_by_date[date]:
                if fb["direction"] != smc["direction"]:
                    conflicts.append({
                        "date": date,
                        "symbol": fb["symbol"],
                        "fb_dir": fb["direction"],
                        "smc_dir": smc["direction"],
                    })

    return {
        "total_fb": len(fb_trades),
        "total_smc_proxy": len(smc_trades),
        "conflict_count": len(conflicts),
        "conflict_pct": round(len(conflicts)/max(len(common),1)*100, 1) if common else 0,
        "conflicts": conflicts[:20],
    }


def regime_composition(trades: List[Dict]) -> Dict:
    """Count trades per regime."""
    comp: Dict[str, int] = {}
    for t in trades:
        r = t.get("regime", "UNKNOWN")
        comp[r] = comp.get(r, 0) + 1
    return comp


def main():
    print("=" * 80)
    print("  DUAL-STRATEGY PORTFOLIO BACKTEST")
    print("  False Breakout Trap  +  SMC 8-Gate (proxy)")
    print("=" * 80)

    all_fb_trades: List[Dict] = []
    all_smc_trades: List[Dict] = []
    per_pair_results: Dict[str, Dict] = {}
    regime_results: Dict[str, Dict] = {}

    for sym in ALL_SYMBOLS:
        print(f"\n  {'=' * 50}")
        print(f"  {sym}")
        print(f"  {'=' * 50}")

        df = load_data(sym)
        if df is None or len(df) < 500:
            print(f"    No data — skipping")
            continue

        # Ensure indicators exist
        if "atr" not in df.columns:
            print(f"    No ATR column — skipping (need precomputed indicators)")
            continue

        # ── Precompute regime (once per symbol) ──
        regs = classify_regime(df)

        # ── FB backtest ──
        fb_trades = backtest_symbol(df, sym)
        print(f"    FB: {len(fb_trades)} trades")

        # Apply spread costs + regime classification
        _, total_cost = compute_costs(sym)
        for t in fb_trades:
            risk = abs(t["entry"] - t["sl"])
            cost_r = total_cost / risk if risk > 0 else 0
            t["net_pnl_r"] = round(t["pnl_r"] - cost_r, 4)
            date = pd.Timestamp(t["entry_date"], tz="UTC")
            mask = df.index <= date
            t["regime"] = str(regs.iloc[mask.sum() - 1]) if mask.any() else "UNKNOWN"

        # Stats
        raw_stats = stats_from_trades(fb_trades, "pnl_r")
        net_stats = stats_from_trades(fb_trades, "net_pnl_r")
        print(f"      Raw PF: {raw_stats['pf']:.3f} | Net PF: {net_stats['pf']:.3f} | WR: {raw_stats['wr']:.1%}")
        print(f"      AvgR: {raw_stats['avg_r']:.4f} | MDD: {raw_stats['mdd_r']:.1f}R | Sharpe: {raw_stats['sharpe']:.2f}")

        # Regime breakdown
        regime_trades: Dict[str, List[Dict]] = {}
        for t in fb_trades:
            regime_trades.setdefault(t["regime"], []).append(t)

        for regime, rt in sorted(regime_trades.items()):
            s = stats_from_trades(rt, "net_pnl_r")
            if s["total_trades"] >= 5:
                regime_results.setdefault(regime, {"trades": [], "count": 0})
                regime_results[regime]["trades"].extend(rt)
                regime_results[regime]["count"] += s["total_trades"]

        per_pair_results[sym] = {
            "fb_trades": len(fb_trades),
            "raw_pf": raw_stats["pf"],
            "net_pf": net_stats["pf"],
            "wr": raw_stats["wr"],
            "avg_r": raw_stats["avg_r"],
            "mdd": raw_stats["mdd_r"],
            "sharpe": raw_stats["sharpe"],
        }
        all_fb_trades.extend(fb_trades)

        # ── SMC Proxy (regime-dependent, trending only) ──
        smc_trades = simulate_smc_proxy(df, sym, precomputed_regime=regs)
        for t in smc_trades:
            t["symbol"] = sym
        all_smc_trades.extend(smc_trades)
        if smc_trades:
            smc_s = stats_from_trades(smc_trades, "pnl_r")
            print(f"    SMC Proxy: {len(smc_trades)} trades | PF: {smc_s['pf']:.3f} | WR: {smc_s['wr']:.1%}")
        else:
            print(f"    SMC Proxy: 0 trades")

    # ── Combined Portfolio Stats ──
    print(f"\n{'=' * 70}")
    print("  COMBINED PORTFOLIO ANALYSIS")
    print(f"{'=' * 70}")

    if all_fb_trades:
        fb_s = stats_from_trades(all_fb_trades, "net_pnl_r")
        print(f"\n  False Breakout (all pairs):")
        print(f"    {fb_s['total_trades']} trades | PF {fb_s['pf']:.3f} | WR {fb_s['wr']:.1%}")
        print(f"    AvgR {fb_s['avg_r']:.4f} | MDD {fb_s['mdd_r']:.1f}R | Sharpe {fb_s['sharpe']:.2f}")

    if all_smc_trades:
        smc_s = stats_from_trades(all_smc_trades, "pnl_r")
        print(f"\n  SMC Proxy (trending-only, all pairs):")
        print(f"    {smc_s['total_trades']} trades | PF {smc_s['pf']:.3f} | WR {smc_s['wr']:.1%}")

    # ── Regime Aggregation ──
    print(f"\n  Regime Performance (FB only):")
    for regime in sorted(regime_results.keys()):
        rr = regime_results[regime]
        s = stats_from_trades(rr["trades"], "net_pnl_r")
        print(f"    {regime:15s}: {s['total_trades']:5d} trades | PF {s['pf']:.3f} | WR {s['wr']:.1%} | AvgR {s['avg_r']:+.4f}")

    # ── Overlap / Conflict Analysis ──
    print(f"\n  Strategy Overlap:")
    ol = find_overlaps(all_fb_trades, all_smc_trades)
    print(f"    FB trades: {ol['total_fb']}")
    print(f"    SMC proxy trades: {ol['total_smc_proxy']}")
    print(f"    Conflicts (opposite dir, same bar): {ol['conflict_count']} ({ol['conflict_pct']}% of common dates)")
    if ol['conflicts']:
        print(f"    Sample conflicts:")
        for c in ol['conflicts'][:5]:
            print(f"      {c['date']} {c['symbol']}: FB {c['fb_dir']} vs SMC {c['smc_dir']}")

    # ── Portfolio Simulation: Regime-Based Selection ──
    print(f"\n  Regime-Based Portfolio Simulation:")
    if all_fb_trades:
        # FB in RANGING, L0W_VOL, MIXED; SMC only in TRENDING/HIGH_VOL
        fb_ranging = [t for t in all_fb_trades if "RANGING" in t.get("regime", "") or "LOW_VOL" in t.get("regime", "") or "MIXED" in t.get("regime", "")]
        fb_other = [t for t in all_fb_trades if t not in fb_ranging]
        smc_trending = [t for t in all_smc_trades if "TRENDING" in t.get("regime", "") or "HIGH_VOL" in t.get("regime", "")]

        if fb_ranging:
            r_s = stats_from_trades(fb_ranging, "net_pnl_r")
            print(f"    FB in RANGING/LOW_VOL/MIXED: {r_s['total_trades']} trades | PF {r_s['pf']:.3f}")
        if smc_trending:
            t_s = stats_from_trades(smc_trending, "pnl_r")
            print(f"    SMC in TRENDING/HIGH_VOL:    {t_s['total_trades']} trades | PF {t_s['pf']:.3f}")

        # Combined — simple concatenation (no weighting)
        combined = fb_ranging + smc_trending
        if combined:
            net_pnls = np.array([t.get("net_pnl_r", t["pnl_r"]) for t in combined])
            wins = net_pnls[net_pnls > 0]; losses = net_pnls[net_pnls < 0]
            comb_pf = float(np.sum(wins)/abs(np.sum(losses))) if np.sum(losses) != 0 else 0
            comb_wr = len(wins)/len(net_pnls) if len(net_pnls) > 0 else 0
            comb_avg = float(np.mean(net_pnls))
            cum = np.cumsum(net_pnls)
            peak = np.maximum.accumulate(cum)
            comb_mdd = float(np.max(peak - cum)) if len(cum) > 0 else 0
            print(f"\n    {'-' * 40}")
            print(f"    COMBINED PORTFOLIO (regime-allocated):")
            print(f"      {len(combined)} trades | PF {comb_pf:.3f} | WR {comb_wr:.1%}")
            print(f"      AvgR {comb_avg:.4f} | MDD {comb_mdd:.1f}R")
            print(f"      FB contribution: {len(fb_ranging)}/{len(combined)} ({len(fb_ranging)/len(combined)*100:.0f}%)")
            print(f"      SMC contribution: {len(smc_trending)}/{len(combined)} ({len(smc_trending)/len(combined)*100:.0f}%)")

    # ── Save ──
    results = {
        "timestamp": datetime.now().isoformat(),
        "per_pair": per_pair_results,
        "fb_overall": stats_from_trades(all_fb_trades, "net_pnl_r") if all_fb_trades else {},
        "smc_proxy_overall": stats_from_trades(all_smc_trades, "pnl_r") if all_smc_trades else {},
        "regime_breakdown": {r: stats_from_trades(rr["trades"], "net_pnl_r") for r, rr in sorted(regime_results.items())},
        "conflicts": ol,
    }

    out_path = OUTPUT_DIR / "dual_strategy_backtest.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
