"""
Layer 11: Backtesting Engine
Historical simulation — win rate, drawdown, RR performance per session.
Run this BEFORE going live. No surprises in production.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    symbol: str
    direction: str
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    confidence: float
    score: int
    session: str
    open_time: object
    close_time: Optional[object] = None
    result: str = "open"       # "win_tp1" | "win_tp2" | "win_tp3" | "loss"
    actual_rr: float = 0.0
    reason: str = ""


@dataclass
class BacktestResult:
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    avg_rr_wins: float
    max_drawdown: float
    profit_factor: float
    by_session: Dict[str, Dict]
    by_symbol: Dict[str, Dict]
    equity_curve: List[float]
    trades: List[BacktestTrade]


def run_backtest(symbol: str, config,
                 start_date: str = "2024-01-01",
                 end_date: str = "2024-12-31",
                 initial_balance: float = 10000.0) -> BacktestResult:
    """
    Full backtest on historical data.
    Fetches OHLCV, runs the complete signal pipeline bar-by-bar,
    simulates trade outcomes, and returns comprehensive stats.
    """
    from data_layer import fetch_ohlcv, add_indicators
    from market_structure import analyze_market_structure
    from entry_logic import find_best_entry
    from scoring_engine import assess_indicators, score_signal, build_risk_profile
    from data_layer import get_current_session

    logger.info(f"Backtesting {symbol} from {start_date} to {end_date}")

    # Fetch full history
    df_full = fetch_ohlcv(symbol, config.PRIMARY_TIMEFRAME, limit=5000,
                           source=config.DATA_SOURCE)
    if df_full is None or len(df_full) < 200:
        logger.error(f"Insufficient historical data for {symbol}")
        return BacktestResult(0, 0, 0, 0, 0, 0, 0, {}, {}, [], [])

    # Filter to date range
    df_full = df_full[
        (df_full.index >= pd.Timestamp(start_date, tz="UTC")) &
        (df_full.index <= pd.Timestamp(end_date, tz="UTC"))
    ]

    df_full = add_indicators(df_full, config)
    n = len(df_full)
    logger.info(f"Running backtest on {n} candles for {symbol}")

    trades: List[BacktestTrade] = []
    balance = initial_balance
    equity_curve = [balance]
    open_trade: Optional[BacktestTrade] = None

    MIN_BARS = 100  # need at least this many bars of history

    for i in range(MIN_BARS, n):
        df_slice = df_full.iloc[:i + 1]
        current_candle = df_full.iloc[i]
        current_price = current_candle["close"]

        # ── Manage open trade ────────────────────────────────────────────────
        if open_trade is not None:
            direction = open_trade.direction

            # Check TP3 first (full exit)
            if direction == "buy":
                if current_candle["high"] >= open_trade.tp3:
                    rr = open_trade.actual_rr or open_trade.tp3 / (open_trade.entry - open_trade.stop_loss) * (open_trade.tp3 - open_trade.entry)
                    open_trade.result = "win_tp3"
                    open_trade.actual_rr = 3.0
                elif current_candle["high"] >= open_trade.tp2:
                    open_trade.result = "win_tp2"
                    open_trade.actual_rr = 2.0
                elif current_candle["high"] >= open_trade.tp1:
                    open_trade.result = "win_tp1"
                    open_trade.actual_rr = 1.0
                elif current_candle["low"] <= open_trade.stop_loss:
                    open_trade.result = "loss"
                    open_trade.actual_rr = -1.0
            else:  # sell
                if current_candle["low"] <= open_trade.tp3:
                    open_trade.result = "win_tp3"
                    open_trade.actual_rr = 3.0
                elif current_candle["low"] <= open_trade.tp2:
                    open_trade.result = "win_tp2"
                    open_trade.actual_rr = 2.0
                elif current_candle["low"] <= open_trade.tp1:
                    open_trade.result = "win_tp1"
                    open_trade.actual_rr = 1.0
                elif current_candle["high"] >= open_trade.stop_loss:
                    open_trade.result = "loss"
                    open_trade.actual_rr = -1.0

            if open_trade.result != "open":
                open_trade.close_time = current_candle.name
                risk_pct = config.DEFAULT_RISK_PCT / 100
                if open_trade.actual_rr > 0:
                    balance += balance * risk_pct * open_trade.actual_rr
                else:
                    balance -= balance * risk_pct
                balance = max(balance, 0)
                equity_curve.append(balance)
                trades.append(open_trade)
                open_trade = None
            continue

        # ── Look for new signal ──────────────────────────────────────────────
        if open_trade is not None:
            continue

        try:
            structure = analyze_market_structure(df_slice, config)

            from market_structure import Trend
            for direction in ["buy", "sell"]:
                # Quick trend filter
                if direction == "buy" and structure.trend == Trend.BEARISH:
                    if structure.last_choch is None or structure.last_choch.direction != "bullish":
                        continue
                if direction == "sell" and structure.trend == Trend.BULLISH:
                    if structure.last_choch is None or structure.last_choch.direction != "bearish":
                        continue

                entry_setup = find_best_entry(df_slice, direction, structure, config)
                if entry_setup is None:
                    continue

                indicator_sig = assess_indicators(df_slice, direction, config)

                # Determine session from candle timestamp
                ts = df_full.index[i]
                hour = ts.hour if hasattr(ts, "hour") else 12
                sessions = config.SESSIONS
                session = "dead_zone"
                if sessions["overlap"]["start"] <= hour < sessions["overlap"]["end"]:
                    session = "overlap"
                elif sessions["london"]["start"] <= hour < sessions["london"]["end"]:
                    session = "london"
                elif sessions["new_york"]["start"] <= hour < sessions["new_york"]["end"]:
                    session = "new_york"
                elif sessions["asia"]["start"] <= hour < sessions["asia"]["end"]:
                    session = "asia"

                if session not in config.ALLOWED_SESSIONS:
                    continue

                score = score_signal(
                    structure, entry_setup, indicator_sig,
                    session=session, news_clear=True, config=config
                )

                if not score.passed:
                    continue

                open_trade = BacktestTrade(
                    symbol=symbol,
                    direction=direction,
                    entry=entry_setup.entry_price,
                    stop_loss=entry_setup.stop_loss,
                    tp1=entry_setup.tp1,
                    tp2=entry_setup.tp2,
                    tp3=entry_setup.tp3,
                    confidence=score.confidence_pct,
                    score=score.total,
                    session=session,
                    open_time=df_full.index[i],
                    reason=entry_setup.reason
                )
                break  # one trade at a time

        except Exception as e:
            logger.debug(f"Backtest signal error at bar {i}: {e}")
            continue

    # ── Compute stats ────────────────────────────────────────────────────────
    closed = [t for t in trades if t.result != "open"]
    if not closed:
        logger.warning(f"No trades found for {symbol} in backtest period")
        return BacktestResult(0, 0, 0, 0, 0, 0, 0, {}, {}, equity_curve, [])

    wins = [t for t in closed if t.result.startswith("win")]
    losses = [t for t in closed if t.result == "loss"]
    win_rate = len(wins) / len(closed) * 100 if closed else 0
    avg_rr = np.mean([t.actual_rr for t in wins]) if wins else 0

    # Max drawdown
    peak = initial_balance
    max_dd = 0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd

    # Profit factor
    gross_profit = sum(t.actual_rr for t in wins) * (initial_balance * config.DEFAULT_RISK_PCT / 100)
    gross_loss = len(losses) * (initial_balance * config.DEFAULT_RISK_PCT / 100)
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # By session
    by_session: Dict[str, Dict] = {}
    for t in closed:
        s = t.session
        if s not in by_session:
            by_session[s] = {"total": 0, "wins": 0}
        by_session[s]["total"] += 1
        if t.result.startswith("win"):
            by_session[s]["wins"] += 1
    for s, d in by_session.items():
        d["win_rate"] = round(d["wins"] / d["total"] * 100, 1) if d["total"] > 0 else 0

    result = BacktestResult(
        total_trades=len(closed),
        wins=len(wins),
        losses=len(losses),
        win_rate=round(win_rate, 1),
        avg_rr_wins=round(float(avg_rr), 2),
        max_drawdown=round(max_dd, 2),
        profit_factor=round(pf, 2),
        by_session=by_session,
        by_symbol={symbol: {"total": len(closed), "win_rate": round(win_rate, 1)}},
        equity_curve=equity_curve,
        trades=closed
    )

    logger.info(f"Backtest complete — {symbol}: {len(closed)} trades, "
                f"WR: {win_rate:.1f}%, Avg RR: {avg_rr:.2f}, "
                f"Max DD: {max_dd:.1f}%, PF: {pf:.2f}")

    return result


def print_backtest_report(result: BacktestResult, symbol: str):
    """Print a formatted backtest report to console."""
    print(f"\n{'='*55}")
    print(f"  BACKTEST REPORT — {symbol}")
    print(f"{'='*55}")
    print(f"  Total Trades:    {result.total_trades}")
    print(f"  Wins:            {result.wins}")
    print(f"  Losses:          {result.losses}")
    print(f"  Win Rate:        {result.win_rate:.1f}%")
    print(f"  Avg RR (wins):   1:{result.avg_rr_wins}")
    print(f"  Max Drawdown:    {result.max_drawdown:.1f}%")
    print(f"  Profit Factor:   {result.profit_factor:.2f}")
    print()
    print("  By Session:")
    for sess, stats in result.by_session.items():
        print(f"    {sess:<12} {stats['total']:>3} trades  WR: {stats['win_rate']:.1f}%")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    from config import CONFIG

    symbols = CONFIG.SYMBOLS if len(sys.argv) < 2 else [sys.argv[1]]
    for sym in symbols:
        result = run_backtest(sym, CONFIG)
        print_backtest_report(result, sym)
