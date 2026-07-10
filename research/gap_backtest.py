"""
Gap Strategy Backtest + Adversarial Validation

Tests MM-002 (Monday Gap Fade) and MM-012 (Gap Fill Weekend)
with full grid sweep, walk-forward, Monte Carlo, bootstrap,
spread stress, trade removal, and regime-conditional analysis.

Usage:
    python research/gap_backtest.py
"""

import os
import sys
import json
import warnings
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# --- Config ----------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

ALL_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "XAUUSD",
    "AUDUSD", "NZDUSD", "USDCAD", "GBPJPY",
]

SPREADS = {
    "EURUSD": 1.2, "GBPUSD": 1.5, "USDJPY": 1.3, "XAUUSD": 3.5,
    "AUDUSD": 1.4, "NZDUSD": 1.8, "USDCAD": 1.3, "GBPJPY": 2.5,
}

PIP_SIZES = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDJPY": 0.01, "XAUUSD": 0.01,
    "AUDUSD": 0.0001, "NZDUSD": 0.0001, "USDCAD": 0.0001, "GBPJPY": 0.01,
}

# ============================================================================
# PHASE 1: Gap Detection Engine
# ============================================================================

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
    gap_atr: float
    gap_pct: float
    gap_type: str
    pnl_r: float
    net_pnl_r: float
    risk: float
    reward: float
    rr: float
    year: int
    params: Dict = field(default_factory=dict)
    regime: str = ""


def load_data(symbol: str) -> Optional[pd.DataFrame]:
    path = DATA_DIR / f"{symbol}_1d.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["Date"])
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Ensure ATR column exists
    if "atr" not in df.columns:
        tr = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                abs(df["high"] - df["close"].shift(1)),
                abs(df["low"] - df["close"].shift(1)),
            ),
        )
        df["atr"] = tr.rolling(14).mean()

    return df


def run_gap_strategy(
    df: pd.DataFrame,
    symbol: str,
    strategy_id: str = "MM-002",
    min_gap_atr_mult: float = 0.3,
    sl_atr_mult: float = 1.0,
    max_hold_bars: int = 5,
    min_gap_pct: float = 0.15,
) -> List[Trade]:
    """
    Run gap strategy on daily data.
    MM-002: ATR-based gap sizing, all pairs.
    MM-012: %-based gap sizing, GBPUSD only.
    """
    if strategy_id == "MM-012" and symbol not in ["GBPUSD"]:
        return []

    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    opens = df["open"].values
    atr_vals = df["atr"].values
    dates = pd.to_datetime(df["Date"])

    trades: List[Trade] = []
    friday_close = None
    friday_idx = -1
    week_trade_taken = False
    current_iso_week = None
    min_start = 20  # warm-up

    for i in range(min_start, len(df) - 1):
        ts = dates[i]
        wd = ts.weekday()

        # Track Friday close
        if wd == 4:
            friday_close = closes[i]
            friday_idx = i

            iso_week = ts.isocalendar()[1]
            if iso_week != current_iso_week:
                current_iso_week = iso_week
                week_trade_taken = False

        # Only trade on Monday
        if wd != 0 or friday_close is None or week_trade_taken:
            continue
        if np.isnan(atr_vals[i]) or atr_vals[i] <= 0:
            continue

        atr_val = atr_vals[i]
        gap = opens[i] - friday_close
        gap_atr = abs(gap) / atr_val if atr_val > 0 else 0
        gap_pct = abs(gap) / friday_close * 100 if friday_close > 0 else 0

        # Filter by gap size
        if strategy_id == "MM-002":
            if gap_atr < min_gap_atr_mult:
                continue
        else:
            if gap_pct < min_gap_pct:
                continue

        entry = opens[i]
        year = ts.year

        if gap > 0:  # Gap up -> short
            sl = entry + atr_val * sl_atr_mult
            tp = friday_close
            direction = "SELL"
        else:  # Gap down -> long
            sl = entry - atr_val * sl_atr_mult
            tp = friday_close
            direction = "BUY"

        risk = abs(entry - sl)
        reward = abs(entry - tp)
        rr = reward / risk if risk > 0 else 0

        # Simulate exit
        exit_price = closes[i]
        exit_reason = "CLOSE_EXIT"

        max_bars = int(max_hold_bars)
        for offset in range(0, min(max_bars + 1, len(df) - i)):
            bi = i + offset
            if bi >= len(df):
                break

            if direction == "BUY":
                if lows[bi] <= sl:
                    exit_price = sl
                    exit_reason = "SL"
                    break
                if highs[bi] >= tp or closes[bi] >= tp:
                    exit_price = tp
                    exit_reason = "TP"
                    break
            else:
                if highs[bi] >= sl:
                    exit_price = sl
                    exit_reason = "SL"
                    break
                if lows[bi] <= tp or closes[bi] <= tp:
                    exit_price = tp
                    exit_reason = "TP"
                    break

            if offset > 0:
                exit_price = closes[bi]
                exit_reason = "TIME_EXIT"

        if direction == "BUY":
            pnl_raw = exit_price - entry
        else:
            pnl_raw = entry - exit_price

        pnl_r = pnl_raw / risk if risk > 0 else 0

        # Apply costs
        pip_size = PIP_SIZES.get(symbol, 0.0001)
        spread_cost = SPREADS.get(symbol, 1.0) * pip_size
        commission = 0.5 * pip_size
        slippage = 0.5 * pip_size
        total_cost = spread_cost + commission + slippage
        net_pnl_r = (pnl_raw - total_cost) / risk if risk > 0 else 0

        trades.append(Trade(
            symbol=symbol,
            entry_date=ts.strftime("%Y-%m-%d"),
            direction=direction,
            entry_price=float(entry),
            sl=float(sl),
            tp=float(tp),
            exit_price=float(exit_price),
            exit_reason=exit_reason,
            gap_atr=round(float(gap_atr), 4),
            gap_pct=round(float(gap_pct), 4),
            gap_type="up" if gap > 0 else "down",
            pnl_r=round(float(pnl_r), 4),
            net_pnl_r=round(float(net_pnl_r), 4),
            risk=float(risk),
            reward=float(reward),
            rr=round(rr, 2),
            year=year,
        ))
        week_trade_taken = True

    return trades


# ============================================================================
# Stats & Reporting
# ============================================================================

def compute_stats(trades: List[Trade], pnl_key: str = "net_pnl_r") -> Dict:
    if not trades:
        return {"total_trades": 0, "wins": 0, "losses": 0, "pf": 0, "wr": 0,
                "avg_r": 0, "mdd_r": 0, "sharpe": 0, "gross_profit": 0, "gross_loss": 0}

    pnls = np.array([getattr(t, pnl_key) for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]

    pf = float(np.sum(wins) / abs(np.sum(losses))) if np.sum(losses) != 0 else 0
    wr = len(wins) / len(pnls) if len(pnls) > 0 else 0
    avg_r = float(np.mean(pnls)) if len(pnls) > 0 else 0

    cum = np.cumsum(pnls)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    mdd = float(np.max(dd)) if len(dd) > 0 else 0

    std = float(np.std(pnls)) if len(pnls) > 1 else 1
    sharpe = float(np.mean(pnls) / std * np.sqrt(52)) if std > 0 else 0

    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "pf": round(pf, 4),
        "wr": round(wr, 4),
        "avg_r": round(avg_r, 4),
        "mdd_r": round(mdd, 2),
        "sharpe": round(sharpe, 4),
        "gross_profit": round(float(np.sum(wins)), 2),
        "gross_loss": round(float(abs(np.sum(losses))), 2),
    }


def print_stats(label: str, stats: Dict):
    print(f"  {label:30s}: {stats['total_trades']:4d} trades | PF {stats['pf']:.3f} | "
          f"WR {stats['wr']:.1%} | AvgR {stats['avg_r']:+.4f} | "
          f"MDD {stats['mdd_r']:.1f}R | Sharpe {stats['sharpe']:.2f}")


# ============================================================================
# PHASE 2: Parameter Grid Sweep
# ============================================================================

def parameter_grid_sweep(
    df: pd.DataFrame,
    symbol: str,
    strategy_id: str = "MM-002",
) -> List[Dict]:
    results = []

    if strategy_id == "MM-002":
        grid = {
            "min_gap_atr_mult": [0.2, 0.3, 0.4, 0.5],
            "sl_atr_mult": [0.8, 1.0, 1.2, 1.5],
            "max_hold_bars": [3, 5, 10],
        }
    else:
        grid = {
            "min_gap_pct": [0.05, 0.10, 0.15, 0.25],
            "sl_atr_mult": [1.0, 1.5, 2.0],
            "max_hold_bars": [3, 5, 10],
        }

    import itertools
    keys = list(grid.keys())
    for values in itertools.product(*grid.values()):
        params = dict(zip(keys, values))
        kw = {"strategy_id": strategy_id}
        if strategy_id == "MM-002":
            kw["min_gap_atr_mult"] = params["min_gap_atr_mult"]
        else:
            kw["min_gap_pct"] = params["min_gap_pct"]
        kw["sl_atr_mult"] = params["sl_atr_mult"]
        kw["max_hold_bars"] = params["max_hold_bars"]

        trades = run_gap_strategy(df, symbol, **kw)
        stats = compute_stats(trades)

        results.append({
            **params,
            "total_trades": stats["total_trades"],
            "pf": stats["pf"],
            "wr": stats["wr"],
            "avg_r": stats["avg_r"],
            "mdd_r": stats["mdd_r"],
            "sharpe": stats["sharpe"],
        })

    return results


# ============================================================================
# PHASE 3: Adversarial Tests
# ============================================================================

def year_by_year_analysis(trades: List[Trade]) -> Dict:
    by_year: Dict[int, List[Trade]] = {}
    for t in trades:
        by_year.setdefault(t.year, []).append(t)
    return {yr: compute_stats(tlist) for yr, tlist in sorted(by_year.items())}


def walk_forward_validation(trades: List[Trade], n_folds: int = 5) -> List[Dict]:
    if len(trades) < 20:
        return []

    trades_sorted = sorted(trades, key=lambda t: t.entry_date)
    fold_size = len(trades_sorted) // (n_folds + 1)
    results = []

    for fold in range(n_folds):
        train_start = fold * fold_size
        train_end = (fold + 1) * fold_size
        test_start = train_end
        test_end = min((fold + 2) * fold_size, len(trades_sorted))

        train_t = trades_sorted[train_start:train_end]
        test_t = trades_sorted[test_start:test_end]

        if len(train_t) < 5 or len(test_t) < 5:
            continue

        train_s = compute_stats(train_t)
        test_s = compute_stats(test_t)

        results.append({
            "fold": fold + 1,
            "train_period": f"{train_t[0].entry_date} -> {train_t[-1].entry_date}",
            "test_period": f"{test_t[0].entry_date} -> {test_t[-1].entry_date}",
            "train_trades": len(train_t),
            "test_trades": len(test_t),
            "train_pf": train_s["pf"],
            "train_wr": train_s["wr"],
            "test_pf": test_s["pf"],
            "test_wr": test_s["wr"],
            "test_avg_r": test_s["avg_r"],
            "degradation": round(test_s["pf"] / train_s["pf"], 2) if train_s["pf"] > 0 else 0,
        })

    return results


def spread_stress_test(trades: List[Trade], symbol: str, mults: List[float] = None) -> Dict:
    if mults is None:
        mults = [1, 2, 3, 5]

    pip_size = PIP_SIZES.get(symbol, 0.0001)
    base_spread = SPREADS.get(symbol, 1.0) * pip_size
    commission = 0.5 * pip_size
    slippage = 0.5 * pip_size
    base_cost = base_spread + commission + slippage

    results = {}
    for mult in mults:
        stressed_cost = base_spread * mult + commission + slippage
        cost_inc = stressed_cost - base_cost

        stressed_trades = []
        for t in trades:
            new_pnl = t.pnl_r - (cost_inc / t.risk) if t.risk > 0 else t.pnl_r
            stressed_trades.append(Trade(
                **{**t.__dict__, "net_pnl_r": round(new_pnl, 4)}
            ))

        stats = compute_stats(stressed_trades)
        results[f"spread_{mult}x"] = stats

    return results


def monte_carlo_validation(
    trades: List[Trade],
    n_sims: int = 10000,
    starting_balance: float = 1000,
    risk_pct: float = 1.0,
) -> Dict:
    pnls = np.array([t.net_pnl_r for t in trades])
    if len(pnls) < 10:
        return {"error": "Insufficient trades"}

    final_balances = []
    max_dds = []
    ruin_count = 0

    for _ in range(n_sims):
        shuffled = np.random.permutation(pnls)
        balance = starting_balance
        peak = balance
        mdd = 0.0

        for r in shuffled:
            risk_amount = balance * (risk_pct / 100.0)
            balance += r * risk_amount
            peak = max(peak, balance)
            dd = (peak - balance) / peak * 100 if peak > 0 else 0
            mdd = max(mdd, dd)
            if balance <= 0:
                ruin_count += 1
                break

        final_balances.append(balance)
        max_dds.append(mdd)

    return {
        "n_simulations": n_sims,
        "prob_ruin": round(ruin_count / n_sims, 6),
        "mean_final_balance": round(float(np.mean(final_balances)), 2),
        "median_final_balance": round(float(np.median(final_balances)), 2),
        "p5_final_balance": round(float(np.percentile(final_balances, 5)), 2),
        "p95_final_balance": round(float(np.percentile(final_balances, 95)), 2),
        "mean_max_dd_pct": round(float(np.mean(max_dds)), 2),
        "p95_max_dd_pct": round(float(np.percentile(max_dds, 95)), 2),
        "p99_max_dd_pct": round(float(np.percentile(max_dds, 99)), 2),
        "still_profitable_pct": round(
            sum(1 for b in final_balances if b > starting_balance) / n_sims * 100, 1
        ),
    }


def bootstrap_monte_carlo(trades: List[Trade], n_sims: int = 10000) -> Dict:
    pnls = np.array([t.net_pnl_r for t in trades])
    if len(pnls) < 10:
        return {"error": "Insufficient trades"}

    pfs, avg_rs, wrs = [], [], []
    for _ in range(n_sims):
        sample = np.random.choice(pnls, size=len(pnls), replace=True)
        wins = sum(r for r in sample if r > 0)
        losses = abs(sum(r for r in sample if r < 0))
        pf = wins / losses if losses > 0 else 10.0
        pfs.append(pf)
        avg_rs.append(float(np.mean(sample)))
        wrs.append(float(sum(1 for r in sample if r > 0) / len(sample)))

    return {
        "n_simulations": n_sims,
        "pf_mean": round(float(np.mean(pfs)), 4),
        "pf_median": round(float(np.median(pfs)), 4),
        "pf_p5": round(float(np.percentile(pfs, 5)), 4),
        "pf_p95": round(float(np.percentile(pfs, 95)), 4),
        "pf_p1": round(float(np.percentile(pfs, 1)), 4),
        "pf_p99": round(float(np.percentile(pfs, 99)), 4),
        "pf_below_1_pct": round(
            sum(1 for p in pfs if p < 1.0) / n_sims * 100, 1
        ),
        "avg_r_mean": round(float(np.mean(avg_rs)), 4),
        "avg_r_p5": round(float(np.percentile(avg_rs, 5)), 4),
        "avg_r_p95": round(float(np.percentile(avg_rs, 95)), 4),
        "wr_mean": round(float(np.mean(wrs)), 4),
        "wr_p5": round(float(np.percentile(wrs, 5)), 4),
    }


def trade_removal_test(
    trades: List[Trade],
    removal_pcts: List[float] = None,
) -> Dict:
    if removal_pcts is None:
        removal_pcts = [0.1, 0.2, 0.3]

    pnls = np.array([t.net_pnl_r for t in trades])
    winners = [i for i, p in enumerate(pnls) if p > 0]
    base_stats = compute_stats(trades)
    results = {"base": base_stats}

    for removal_pct in removal_pcts:
        n_remove = max(1, int(len(winners) * removal_pct))
        surviving_pfs = []

        for _ in range(1000):
            remove_indices = set(
                np.random.choice(winners, size=n_remove, replace=False)
            )
            remaining = [p for i, p in enumerate(pnls) if i not in remove_indices]
            w = sum(p for p in remaining if p > 0)
            l = abs(sum(p for p in remaining if p < 0))
            pf = w / l if l > 0 else 0
            surviving_pfs.append(pf)

        results[f"remove_{int(removal_pct*100)}pct_winners"] = {
            "mean_pf": round(float(np.mean(surviving_pfs)), 4),
            "median_pf": round(float(np.median(surviving_pfs)), 4),
            "pf_below_1_pct": round(
                sum(1 for p in surviving_pfs if p < 1.0) / len(surviving_pfs) * 100, 1
            ),
            "p5_pf": round(float(np.percentile(surviving_pfs, 5)), 4),
            "n_winners_removed": n_remove,
        }

    return results


# ============================================================================
# PHASE 4: Regime-Conditional Analysis
# ============================================================================

def classify_regime(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    atr_vals = df["atr"].values

    # Trend strength: rate of change normalized by ATR
    trend_strength = np.full(len(closes), np.nan)
    for i in range(lookback, len(closes)):
        if not np.isnan(atr_vals[i]) and atr_vals[i] > 0:
            roc = (closes[i] - closes[i - lookback]) / closes[i - lookback]
            trend_strength[i] = abs(roc) / (atr_vals[i] / closes[i])

    # Volatility rank (rolling percentile)
    vol_rank = np.full(len(closes), np.nan)
    for i in range(lookback * 3, len(closes)):
        window = atr_vals[i - lookback * 3 : i]
        valid = window[~np.isnan(window)]
        if len(valid) > 10 and not np.isnan(atr_vals[i]):
            vol_rank[i] = sum(v < atr_vals[i] for v in valid) / len(valid)

    regimes = pd.Series("UNCLASSIFIED", index=df.index)
    for i in range(lookback * 3, len(df)):
        ts_val = np.nan_to_num(trend_strength[i], nan=0)
        vr_val = np.nan_to_num(vol_rank[i], nan=0.5)

        if ts_val > 1.5:
            primary = "TRENDING"
        elif ts_val < 0.5:
            primary = "RANGING"
        else:
            primary = "MIXED"

        vol_label = ""
        if vr_val > 0.75:
            vol_label = "HIGH_VOL"
        elif vr_val < 0.25:
            vol_label = "LOW_VOL"

        regime = primary if not vol_label else vol_label
        regimes.iloc[i] = regime

    return regimes


def regime_conditional_analysis(trades: List[Trade], df: pd.DataFrame) -> Dict:
    regimes = classify_regime(df)
    regime_trades: Dict[str, List[Trade]] = {}

    for t in trades:
        date = pd.Timestamp(t.entry_date, tz="UTC")
        mask = df["Date"] <= date
        if not mask.any():
            continue
        closest_pos = mask.sum() - 1
        if closest_pos < 0:
            continue
        regime = regimes.iloc[closest_pos]

        regime_trades.setdefault(regime, []).append(t)
        t.regime = regime

    return {
        regime: compute_stats(tlist)
        for regime, tlist in sorted(regime_trades.items())
    }


# ============================================================================
# Main Orchestration
# ============================================================================

def run_adversarial_suite(
    trades: List[Trade],
    symbol: str,
    df: pd.DataFrame,
    label: str = "",
) -> Dict:
    results: Dict[str, Any] = {}

    if not trades:
        print(f"  [{label}] No trades generated. Skipping adversarial tests.")
        return results

    # Baseline
    stats = compute_stats(trades)
    results["baseline"] = stats
    print_stats(f"[{label}] Baseline", stats)

    # Year-by-year
    print(f"\n  [{label}] Year-by-Year:")
    yby = year_by_year_analysis(trades)
    results["year_by_year"] = yby
    for yr, s in yby.items():
        print(f"    {yr}: {s['total_trades']:3d} trades | PF {s['pf']:.3f} | WR {s['wr']:.1%} | AvgR {s['avg_r']:+.4f}")

    years_pf_below_1 = sum(1 for s in yby.values() if s["pf"] < 1.0 and s["total_trades"] >= 5)
    results["years_pf_below_1_count"] = years_pf_below_1

    # Walk-forward
    print(f"\n  [{label}] Walk-Forward (5-fold):")
    wf = walk_forward_validation(trades, n_folds=5)
    results["walk_forward"] = wf
    for fold in wf:
        print(f"    Fold {fold['fold']}: Train PF {fold['train_pf']:.3f} -> Test PF {fold['test_pf']:.3f} (deg: {fold['degradation']:.2f}x)")

    avg_test_pf = np.mean([f["test_pf"] for f in wf]) if wf else 0
    all_positive = all(f["test_pf"] > 1.0 for f in wf)
    results["wf_avg_test_pf"] = round(float(avg_test_pf), 4)
    results["wf_all_positive"] = all_positive

    # Spread stress
    print(f"\n  [{label}] Spread Stress:")
    stress = spread_stress_test(trades, symbol)
    results["spread_stress"] = stress
    for k, s in stress.items():
        print(f"    {k:12s}: PF {s['pf']:.4f} | WR {s['wr']:.1%} | AvgR {s['avg_r']:+.4f}")

    stress_survives = all(s["pf"] > 1.0 for s in stress.values())
    stress_pf_at_3x = stress.get("spread_3x", {}).get("pf", 0)
    results["stress_survives_3x"] = stress_pf_at_3x > 1.0

    # Monte Carlo
    print(f"\n  [{label}] Monte Carlo (10,000 sims):")
    mc = monte_carlo_validation(trades, n_sims=10000)
    results["monte_carlo"] = mc
    if "error" not in mc:
        print(f"    P(Ruin): {mc['prob_ruin']:.4f}")
        print(f"    Mean Final: ${mc['mean_final_balance']:.2f} | Median: ${mc['median_final_balance']:.2f}")
        print(f"    P95 Max DD: {mc['p95_max_dd_pct']:.1f}%")
        print(f"    Still Profitable: {mc['still_profitable_pct']:.1f}%")

    mc_survives = mc.get("prob_ruin", 1) < 0.05 and mc.get("p95_max_dd_pct", 100) < 30
    results["mc_survives"] = mc_survives

    # Bootstrap
    print(f"\n  [{label}] Bootstrap MC (10,000 resamples):")
    bmc = bootstrap_monte_carlo(trades, n_sims=10000)
    results["bootstrap_mc"] = bmc
    if "error" not in bmc:
        print(f"    PF Mean: {bmc['pf_mean']:.4f} | Median: {bmc['pf_median']:.4f}")
        print(f"    PF P5-P95: [{bmc['pf_p5']:.4f}, {bmc['pf_p95']:.4f}]")
        print(f"    P(PF < 1.0): {bmc['pf_below_1_pct']:.1f}%")
        print(f"    Avg R Mean: {bmc['avg_r_mean']:.4f} | P5: {bmc['avg_r_p5']:.4f}")

    bmc_survives = bmc.get("pf_p5", 0) > 0.9
    results["bmc_survives"] = bmc_survives

    # Trade removal
    print(f"\n  [{label}] Trade Removal Test:")
    removal = trade_removal_test(trades)
    results["trade_removal"] = removal
    for k, s in removal.items():
        if k == "base":
            print(f"    Base:     PF {s['pf']:.4f} | WR {s['wr']:.1%}")
        else:
            print(f"    {k:20s}: PF {s['mean_pf']:.4f} (P5: {s['p5_pf']:.4f}) | PF<1: {s['pf_below_1_pct']:.1f}%")

    removal_survives = removal.get("remove_10pct_winners", {}).get("pf_below_1_pct", 100) < 50
    results["removal_survives_10pct"] = removal_survives

    # Regime analysis
    print(f"\n  [{label}] Regime-Conditional:")
    regime_res = regime_conditional_analysis(trades, df)
    results["regime_analysis"] = regime_res
    for reg, s in sorted(regime_res.items()):
        print(f"    {reg:15s}: {s['total_trades']:3d} trades | PF {s['pf']:.3f} | WR {s['wr']:.1%} | AvgR {s['avg_r']:+.4f}")

    # Gap direction
    print(f"\n  [{label}] Gap Direction:")
    up_t = [t for t in trades if t.gap_type == "up"]
    dn_t = [t for t in trades if t.gap_type == "down"]
    if up_t:
        print_stats("    Gap Up (short)", compute_stats(up_t))
    if dn_t:
        print_stats("    Gap Down (long)", compute_stats(dn_t))
    results["gap_up"] = compute_stats(up_t)
    results["gap_down"] = compute_stats(dn_t)

    return results


def make_verdict(adv_results: Dict) -> str:
    """Score 0-6 based on how many tests the strategy survives."""
    score = 0
    details = []

    # 1. Baseline PF > 1.1
    if adv_results.get("baseline", {}).get("pf", 0) > 1.1:
        score += 1
        details.append("PF>1.1")
    else:
        details.append("PF<=1.1")

    # 2. Walk-forward: avg test PF > 1.0 AND all folds positive
    wf_ok = adv_results.get("wf_all_positive", False) and adv_results.get("wf_avg_test_pf", 0) > 1.0
    if wf_ok:
        score += 1
        details.append("WF+")
    else:
        details.append("WF-")

    # 3. Spread stress survives 3x
    if adv_results.get("stress_survives_3x", False):
        score += 1
        details.append("Spread+")
    else:
        details.append("Spread-")

    # 4. Monte Carlo: ruin < 5% and P95 DD < 30%
    if adv_results.get("mc_survives", False):
        score += 1
        details.append("MC+")
    else:
        details.append("MC-")

    # 5. Bootstrap: PF P5 > 0.9
    if adv_results.get("bmc_survives", False):
        score += 1
        details.append("Bootstrap+")
    else:
        details.append("Bootstrap-")

    # 6. Trade removal: survive 10% winner removal
    if adv_results.get("removal_survives_10pct", False):
        score += 1
        details.append("Removal+")
    else:
        details.append("Removal-")

    if score >= 5:
        return f"PASS ({score}/6): {', '.join(details)}"
    elif score >= 3:
        return f"MARGINAL ({score}/6): {', '.join(details)}"
    else:
        return f"FAIL ({score}/6): {', '.join(details)}"


def main():
    print("=" * 80)
    print("  GAP STRATEGY BACKTEST + ADVERSARIAL VALIDATION")
    print("=" * 80)

    all_results: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "strategies": {},
    }

    for strategy_id in ["MM-002", "MM-012"]:
        print(f"\n{'#' * 80}")
        print(f"  STRATEGY: {strategy_id}")
        print(f"{'#' * 80}")

        strategy_results: Dict[str, Any] = {}
        best_params_overall = None
        best_pf_overall = 0

        for symbol in ALL_PAIRS:
            print(f"\n{'-' * 60}")
            print(f"  {symbol}")
            print(f"{'-' * 60}")

            df = load_data(symbol)
            if df is None or len(df) < 200:
                print(f"  {symbol}: No data or insufficient data")
                continue

            # Grid sweep
            print(f"  Running parameter grid sweep...")
            grid_results = parameter_grid_sweep(df, symbol, strategy_id)

            if not grid_results:
                continue

            df_grid = pd.DataFrame(grid_results)
            df_grid = df_grid[df_grid["total_trades"] >= 10].sort_values("pf", ascending=False)

            if df_grid.empty:
                continue

            best_row = df_grid.iloc[0].to_dict()
            best_params = {k: best_row[k] for k in best_row
                           if k in ["min_gap_atr_mult", "min_gap_pct", "sl_atr_mult", "max_hold_bars"]}

            print(f"  Best params: {best_params}")
            print(f"  Best PF: {best_row['pf']:.4f} | WR: {best_row['wr']:.1%} | "
                  f"Trades: {int(best_row['total_trades'])}")

            if best_row["pf"] > best_pf_overall:
                best_pf_overall = best_row["pf"]
                best_params_overall = (symbol, best_params)

            # Save per-pair result
            strategy_results[symbol] = {
                "best_params": best_params,
                "best_stats": {k: best_row[k] for k in best_row
                               if k in ["total_trades", "pf", "wr", "avg_r", "mdd_r", "sharpe"]},
                "grid_top5": df_grid.head(5).to_dict("records"),
            }

        # Run adversarial suite on the BEST pair
        if best_params_overall:
            best_sym, best_params = best_params_overall
            print(f"\n{'=' * 60}")
            print(f"  ADVERSARIAL VALIDATION on {best_sym} (best pair)")
            print(f"  Params: {best_params}")
            print(f"{'=' * 60}")

            df = load_data(best_sym)
            kw = {"strategy_id": strategy_id, **best_params}
            trades = run_gap_strategy(df, best_sym, **kw)

            if trades:
                adv_results = run_adversarial_suite(trades, best_sym, df, label=f"{strategy_id}@{best_sym}")
                strategy_results["adversarial"] = adv_results
                strategy_results["adversarial_pair"] = best_sym
                strategy_results["adversarial_params"] = best_params

                verdict = make_verdict(adv_results)
                print(f"\n  >>> VERDICT [{strategy_id}]: {verdict}")
                strategy_results["verdict"] = verdict

        all_results["strategies"][strategy_id] = strategy_results

    # --- Save ---------------------------------------------------------------
    output_path = OUTPUT_DIR / "gap_backtest_results.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Full results saved to {output_path}")
    print("Done.")


if __name__ == "__main__":
    main()
