"""
Full Pipeline Backtester
Runs the entire signal generation pipeline on historical CSV data.
Includes: strategies, scoring, spread/slippage, equity curve, walk-forward.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config import CONFIG
from market_structure import analyze_market_structure, Trend
from entry_logic import find_best_entry
from scoring_engine import assess_indicators, score_signal
from strategies import assess_strategies, get_pair_config

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ── Cost Model ────────────────────────────────────────────────────────────────
# Spread + slippage in price units (not pips)
COSTS = {
    "XAUUSD": {"spread": 0.50, "slippage": 0.25},   # gold: ~$0.75 total
    "EURUSD": {"spread": 0.00015, "slippage": 0.00005},  # ~1.5 pips
    "GBPUSD": {"spread": 0.00020, "slippage": 0.00005},  # ~2.0 pips
    "USDJPY": {"spread": 0.020, "slippage": 0.005},      # ~2.0 pips
    "GBPJPY": {"spread": 0.030, "slippage": 0.005},      # ~3.0 pips
}


@dataclass
class Trade:
    symbol: str
    direction: str
    entry: float
    entry_with_cost: float  # entry + spread/slippage
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    confidence: float
    score: int
    session: str
    day: str
    open_bar: int
    close_bar: int = 0
    result: str = "open"
    actual_rr: float = 0.0
    pnl: float = 0.0
    reason: str = ""
    strategy_confluence: str = ""
    day_filter: str = ""


@dataclass
class BacktestStats:
    symbol: str
    period: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_rr: float = 0.0
    profit_factor: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    expectancy: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_hold_bars: float = 0.0
    by_session: Dict = field(default_factory=dict)
    by_day: Dict = field(default_factory=dict)
    by_strategy: Dict = field(default_factory=dict)
    equity_curve: List[float] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)


def load_data(symbol: str, timeframe: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{symbol}_{timeframe}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df


def get_session(hour: int, config) -> str:
    sessions = config.SESSIONS
    if sessions["overlap"]["start"] <= hour < sessions["overlap"]["end"]:
        return "overlap"
    elif sessions["london"]["start"] <= hour < sessions["london"]["end"]:
        return "london"
    elif sessions["new_york"]["start"] <= hour < sessions["new_york"]["end"]:
        return "new_york"
    elif sessions["asia"]["start"] <= hour < sessions["asia"]["end"]:
        return "asia"
    return "dead_zone"


def run_pipeline_backtest(
    symbol: str,
    config,
    timeframe: str = "1h",
    start_date: str = None,
    end_date: str = None,
    initial_balance: float = 10000.0,
    risk_pct: float = 1.0,
    max_hold_bars: int = 48,
) -> BacktestStats:
    """
    Full pipeline backtest on CSV data.
    Runs the ENTIRE signal generation pipeline including strategies.
    """
    df = load_data(symbol, timeframe)
    if df.empty or len(df) < 250:
        print(f"  Skipping {symbol} — insufficient data")
        return BacktestStats(symbol=symbol, period=f"{start_date} to {end_date}")

    # Filter date range
    if start_date:
        df = df[df.index >= pd.Timestamp(start_date, tz="UTC")]
    if end_date:
        df = df[df.index <= pd.Timestamp(end_date, tz="UTC")]

    if len(df) < 200:
        print(f"  Skipping {symbol} — insufficient data after date filter")
        return BacktestStats(symbol=symbol, period=f"{start_date} to {end_date}")

    n = len(df)
    print(f"  {symbol} [{timeframe}]: {n} bars ({df.index[0].date()} to {df.index[-1].date()})")

    costs = COSTS.get(symbol, {"spread": 0.00010, "slippage": 0.00005})
    pair_cfg = get_pair_config(symbol)

    trades: List[Trade] = []
    balance = initial_balance
    equity_curve = [balance]
    open_trade: Optional[Trade] = None

    MIN_BARS = 200  # need 200 bars for ema_200

    for i in range(MIN_BARS, n):
        df_slice = df.iloc[:i + 1]
        candle = df.iloc[i]
        hour = candle["hour"] if "hour" in df.columns else candle.name.hour
        day_name = candle.name.day_name()

        # ── Manage open trade ────────────────────────────────────────────────
        if open_trade is not None:
            direction = open_trade.direction
            hit_sl = False
            hit_tp = 0

            if direction == "buy":
                # Check SL first (worst case)
                if candle["low"] <= open_trade.stop_loss:
                    hit_sl = True
                    # Apply slippage to SL exit
                    exit_price = open_trade.stop_loss - costs["slippage"]
                    pnl = (exit_price - open_trade.entry_with_cost) / open_trade.entry_with_cost * 100
                    open_trade.result = "loss"
                    open_trade.actual_rr = -1.0
                elif candle["high"] >= open_trade.tp3:
                    hit_tp = 3
                elif candle["high"] >= open_trade.tp2:
                    hit_tp = 2
                elif candle["high"] >= open_trade.tp1:
                    hit_tp = 1
            else:  # sell
                if candle["high"] >= open_trade.stop_loss:
                    hit_sl = True
                    exit_price = open_trade.stop_loss + costs["slippage"]
                    pnl = (open_trade.entry_with_cost - exit_price) / open_trade.entry_with_cost * 100
                    open_trade.result = "loss"
                    open_trade.actual_rr = -1.0
                elif candle["low"] <= open_trade.tp3:
                    hit_tp = 3
                elif candle["low"] <= open_trade.tp2:
                    hit_tp = 2
                elif candle["low"] <= open_trade.tp1:
                    hit_tp = 1

            if hit_tp > 0:
                tp_prices = {1: open_trade.tp1, 2: open_trade.tp2, 3: open_trade.tp3}
                exit_price = tp_prices[hit_tp]
                if direction == "buy":
                    pnl = (exit_price - open_trade.entry_with_cost) / open_trade.entry_with_cost * 100
                else:
                    pnl = (open_trade.entry_with_cost - exit_price) / open_trade.entry_with_cost * 100
                open_trade.result = f"win_tp{hit_tp}"
                open_trade.actual_rr = float(hit_tp)

            if open_trade.result != "open":
                open_trade.close_bar = i
                # Apply P&L
                trade_pnl = balance * (risk_pct / 100) * open_trade.actual_rr
                # Subtract costs (spread already in entry, slippage on exit)
                total_cost = balance * (risk_pct / 100) * (costs["spread"] + costs["slippage"]) / open_trade.entry
                trade_pnl -= total_cost
                balance += trade_pnl
                balance = max(balance, 0)
                open_trade.pnl = trade_pnl
                equity_curve.append(balance)
                trades.append(open_trade)
                open_trade = None
            continue

        # ── Look for new signal ──────────────────────────────────────────────
        try:
            structure = analyze_market_structure(df_slice, config)

            for direction in ["buy", "sell"]:
                # Trend filter
                if direction == "buy" and structure.trend == Trend.BEARISH:
                    if structure.last_choch is None or structure.last_choch.direction != "bullish":
                        continue
                if direction == "sell" and structure.trend == Trend.BULLISH:
                    if structure.last_choch is None or structure.last_choch.direction != "bearish":
                        continue

                # Entry logic
                entry_setup = find_best_entry(df_slice, direction, structure, config)
                if entry_setup is None:
                    continue

                # Indicators
                indicator_sig = assess_indicators(df_slice, direction, config)

                # Strategy confluence (per-pair, with day filter)
                strategy_conv = assess_strategies(df_slice, direction, config, symbol=symbol)

                # Skip on avoid days
                if strategy_conv.day_filter == "avoid":
                    continue

                # Session filter
                session = get_session(int(hour), config)
                if session not in config.ALLOWED_SESSIONS:
                    continue

                # Scoring
                score = score_signal(
                    structure, entry_setup, indicator_sig,
                    session=session, news_clear=True, config=config,
                    strategy_confluence=strategy_conv
                )

                if not score.passed:
                    continue

                # Apply spread/slippage to entry
                if direction == "buy":
                    entry_with_cost = entry_setup.entry_price + costs["spread"] + costs["slippage"]
                else:
                    entry_with_cost = entry_setup.entry_price - costs["spread"] - costs["slippage"]

                open_trade = Trade(
                    symbol=symbol,
                    direction=direction,
                    entry=entry_setup.entry_price,
                    entry_with_cost=entry_with_cost,
                    stop_loss=entry_setup.stop_loss,
                    tp1=entry_setup.tp1,
                    tp2=entry_setup.tp2,
                    tp3=entry_setup.tp3,
                    confidence=score.confidence_pct,
                    score=score.total,
                    session=session,
                    day=day_name,
                    open_bar=i,
                    reason=entry_setup.reason,
                    strategy_confluence=f"{strategy_conv.confluence_direction} ({strategy_conv.confluence_score}/3)",
                    day_filter=strategy_conv.day_filter,
                )
                break  # one trade at a time

        except Exception as e:
            continue

    # ── Compute stats ────────────────────────────────────────────────────────
    closed = [t for t in trades if t.result != "open"]
    stats = BacktestStats(
        symbol=symbol,
        period=f"{df.index[0].date()} to {df.index[-1].date()}",
        equity_curve=equity_curve,
        trades=closed,
    )

    if not closed:
        return stats

    wins = [t for t in closed if t.result.startswith("win")]
    losses = [t for t in closed if t.result == "loss"]

    stats.total_trades = len(closed)
    stats.wins = len(wins)
    stats.losses = len(losses)
    stats.win_rate = round(len(wins) / len(closed) * 100, 1) if closed else 0

    # Win/loss amounts
    win_pnls = [t.pnl for t in wins]
    loss_pnls = [t.pnl for t in losses]
    stats.avg_win = round(np.mean(win_pnls), 2) if win_pnls else 0
    stats.avg_loss = round(np.mean(loss_pnls), 2) if loss_pnls else 0
    stats.avg_rr = round(np.mean([t.actual_rr for t in wins]), 2) if wins else 0

    # Profit factor
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    stats.profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf")

    # Total return
    stats.total_return_pct = round((balance - initial_balance) / initial_balance * 100, 2)

    # Max drawdown
    peak = initial_balance
    max_dd = 0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd
    stats.max_drawdown_pct = round(max_dd, 2)

    # Expectancy
    stats.expectancy = round(
        (stats.win_rate / 100 * stats.avg_win) + ((1 - stats.win_rate / 100) * stats.avg_loss), 2
    )

    # Best/worst trade
    stats.best_trade = round(max(t.pnl for t in closed), 2)
    stats.worst_trade = round(min(t.pnl for t in closed), 2)

    # Avg hold bars
    stats.avg_hold_bars = round(np.mean([t.close_bar - t.open_bar for t in closed]), 1)

    # Sharpe ratio (simplified)
    returns = [t.pnl / initial_balance * 100 for t in closed]
    if returns and np.std(returns) > 0:
        stats.sharpe_ratio = round(np.mean(returns) / np.std(returns), 3)

    # By session
    for t in closed:
        s = t.session
        if s not in stats.by_session:
            stats.by_session[s] = {"total": 0, "wins": 0, "pnl": 0}
        stats.by_session[s]["total"] += 1
        stats.by_session[s]["pnl"] += t.pnl
        if t.result.startswith("win"):
            stats.by_session[s]["wins"] += 1
    for s, d in stats.by_session.items():
        d["win_rate"] = round(d["wins"] / d["total"] * 100, 1) if d["total"] > 0 else 0
        d["pnl"] = round(d["pnl"], 2)

    # By day
    for t in closed:
        d = t.day
        if d not in stats.by_day:
            stats.by_day[d] = {"total": 0, "wins": 0, "pnl": 0}
        stats.by_day[d]["total"] += 1
        stats.by_day[d]["pnl"] += t.pnl
        if t.result.startswith("win"):
            stats.by_day[d]["wins"] += 1
    for d_name, d in stats.by_day.items():
        d["win_rate"] = round(d["wins"] / d["total"] * 100, 1) if d["total"] > 0 else 0
        d["pnl"] = round(d["pnl"], 2)

    # By strategy confluence direction
    for t in closed:
        sc = t.strategy_confluence.split(" ")[0] if t.strategy_confluence else "neutral"
        if sc not in stats.by_strategy:
            stats.by_strategy[sc] = {"total": 0, "wins": 0, "pnl": 0}
        stats.by_strategy[sc]["total"] += 1
        stats.by_strategy[sc]["pnl"] += t.pnl
        if t.result.startswith("win"):
            stats.by_strategy[sc]["wins"] += 1
    for s, d in stats.by_strategy.items():
        d["win_rate"] = round(d["wins"] / d["total"] * 100, 1) if d["total"] > 0 else 0
        d["pnl"] = round(d["pnl"], 2)

    return stats


def print_report(stats: BacktestStats):
    """Print formatted backtest report."""
    print(f"\n{'='*65}")
    print(f"  {stats.symbol} — {stats.period}")
    print(f"{'='*65}")
    print(f"  Trades:       {stats.total_trades}")
    print(f"  Wins/Losses:  {stats.wins}/{stats.losses}")
    print(f"  Win Rate:     {stats.win_rate}%")
    print(f"  Avg RR (wins): 1:{stats.avg_rr}")
    print(f"  Profit Factor: {stats.profit_factor}")
    print(f"  Total Return:  {stats.total_return_pct}%")
    print(f"  Max Drawdown:  {stats.max_drawdown_pct}%")
    print(f"  Sharpe Ratio:  {stats.sharpe_ratio}")
    print(f"  Expectancy:    ${stats.expectancy:+.2f} per trade")
    print(f"  Best Trade:    ${stats.best_trade:+.2f}")
    print(f"  Worst Trade:   ${stats.worst_trade:+.2f}")
    print(f"  Avg Hold:      {stats.avg_hold_bars} bars")

    if stats.by_session:
        print(f"\n  By Session:")
        for sess, d in sorted(stats.by_session.items()):
                print(f"    {sess:<12} {d['total']:>3} trades  WR: {d['win_rate']:>5.1f}%  P&L: ${d['pnl']:>+8.2f}")

    if stats.by_day:
        print(f"\n  By Day:")
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days_order:
            if day in stats.by_day:
                d = stats.by_day[day]
                print(f"    {day:<12} {d['total']:>3} trades  WR: {d['win_rate']:>5.1f}%  P&L: ${d['pnl']:>+8.2f}")

    if stats.by_strategy:
        print(f"\n  By Strategy Direction:")
        for s, d in sorted(stats.by_strategy.items()):
            print(f"    {s:<12} {d['total']:>3} trades  WR: {d['win_rate']:>5.1f}%  P&L: ${d['pnl']:>+8.2f}")

    print(f"{'='*65}")


def save_equity_curve(stats: BacktestStats, filepath: str):
    """Save equity curve to CSV."""
    df = pd.DataFrame({
        "bar": range(len(stats.equity_curve)),
        "balance": stats.equity_curve,
    })
    df.to_csv(filepath, index=False)
    print(f"  Equity curve saved to {filepath}")


def save_trades(stats: BacktestStats, filepath: str):
    """Save trade log to CSV."""
    rows = []
    for t in stats.trades:
        rows.append({
            "symbol": t.symbol,
            "direction": t.direction,
            "entry": t.entry,
            "entry_with_cost": round(t.entry_with_cost, 5),
            "stop_loss": t.stop_loss,
            "tp1": t.tp1,
            "tp2": t.tp2,
            "tp3": t.tp3,
            "result": t.result,
            "rr": t.actual_rr,
            "pnl_pct": round(t.pnl, 2),
            "confidence": t.confidence,
            "score": t.score,
            "session": t.session,
            "day": t.day,
            "hold_bars": t.close_bar - t.open_bar,
            "strategy": t.strategy_confluence,
            "day_filter": t.day_filter,
            "reason": t.reason,
            "open_bar": t.open_bar,
            "close_bar": t.close_bar,
        })
    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False)
    print(f"  Trade log saved to {filepath}")


def run_walk_forward(symbol: str, config, timeframe: str = "1h",
                     initial_balance: float = 10000.0):
    """
    Walk-forward validation: train on first period, test on second.
    Fold 1: Train Jul 2024 - Jun 2025, Test Jul 2025 - Jan 2026
    Fold 2: Train Jul 2024 - Dec 2024, Test Jan 2025 - Jul 2025
    """
    print(f"\n{'='*65}")
    print(f"  WALK-FORWARD: {symbol}")
    print(f"{'='*65}")

    folds = [
        ("Fold 1", "2025-07-01", "2025-12-31", "2026-01-01", "2026-07-03"),
        ("Fold 2", "2025-01-01", "2025-06-30", "2025-07-01", "2025-12-31"),
    ]

    for fold_name, train_start, train_end, test_start, test_end in folds:
        print(f"\n  --- {fold_name} ---")
        print(f"  Train: {train_start} to {train_end}")
        print(f"  Test:  {test_start} to {test_end}")

        # Test on OOS period
        stats = run_pipeline_backtest(
            symbol, config, timeframe,
            start_date=test_start, end_date=test_end,
            initial_balance=initial_balance
        )
        print_report(stats)

        if stats.trades:
            outpath = os.path.join(DATA_DIR, f"{symbol}_{fold_name.replace(' ', '_').lower()}_trades.csv")
            save_trades(stats, outpath)


def main():
    import time
    print("=" * 65)
    print("  FULL PIPELINE BACKTESTER")
    print("  Costs: Spread + Slippage | Strategies: Per-pair + Day filters")
    print("=" * 65)

    symbols = CONFIG.SYMBOLS
    timeframe = "1h"
    initial_balance = 10000.0

    # ── Full period backtest (6 months) ───────────────────────────────────────
    print("\n--- FULL PERIOD BACKTEST (Jan-Jul 2026) ---")
    all_stats = []
    t_start = time.time()

    for idx, symbol in enumerate(symbols, 1):
        t_sym = time.time()
        print(f"\n[{idx}/{len(symbols)}] Backtesting {symbol}...")
        stats = run_pipeline_backtest(
            symbol, CONFIG, timeframe,
            start_date="2026-01-01", end_date="2026-07-03",
            initial_balance=initial_balance
        )
        print_report(stats)
        all_stats.append(stats)

        if stats.trades:
            save_equity_curve(stats, os.path.join(DATA_DIR, f"{symbol}_equity.csv"))
            save_trades(stats, os.path.join(DATA_DIR, f"{symbol}_trades.csv"))

        elapsed = time.time() - t_sym
        total_elapsed = time.time() - t_start
        remaining = (len(symbols) - idx) * elapsed
        print(f"  [{symbol}] Done in {elapsed:.0f}s | ETA: {remaining/60:.1f}min remaining")

    # ── Portfolio summary ─────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  PORTFOLIO SUMMARY")
    print(f"{'='*65}")
    total_trades = sum(s.total_trades for s in all_stats)
    total_wins = sum(s.wins for s in all_stats)
    total_losses = sum(s.losses for s in all_stats)
    total_pnl = sum(s.total_return_pct for s in all_stats)
    avg_wr = total_wins / total_trades * 100 if total_trades > 0 else 0
    avg_dd = np.mean([s.max_drawdown_pct for s in all_stats if s.max_drawdown_pct > 0]) if all_stats else 0

    print(f"  Total Trades:  {total_trades}")
    print(f"  Win Rate:      {avg_wr:.1f}%")
    print(f"  Combined P&L:  {total_pnl:+.2f}%")
    print(f"  Avg Max DD:    {avg_dd:.1f}%")

    for s in all_stats:
        if s.total_trades > 0:
            print(f"  {s.symbol:<8} {s.total_trades:>3} trades  WR: {s.win_rate:>5.1f}%  "
                  f"PF: {s.profit_factor:>5.2f}  P&L: {s.total_return_pct:>+8.2f}%  DD: {s.max_drawdown_pct:.1f}%")

    print(f"{'='*65}")

    # ── Walk-forward ──────────────────────────────────────────────────────────
    print("\n--- WALK-FORWARD VALIDATION ---")
    for symbol in symbols:
        run_walk_forward(symbol, CONFIG, timeframe, initial_balance)

    print(f"\nTotal time: {(time.time() - t_start)/60:.1f} minutes")


if __name__ == "__main__":
    main()
