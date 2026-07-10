"""
False Breakout Trap — Secondary Signal Generator.
Detects price breaking a swing high/low then reversing within 2 bars.
Counter-trend strategy optimised for ranging / quiet regimes.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def detect_false_breakouts(
    df: pd.DataFrame,
    lookback: int = 10,
    sl_atr_mult: float = 1.0,
    tp1_atr_mult: float = 1.5,
    tp2_atr_mult: float = 2.5,
    tp3_atr_mult: float = 3.5,
    symbol: str = "",
) -> List[Dict]:
    """
    Scan the last 3 bars for a completed false-breakout pattern.

    Returns 0 or 1 signal dict with keys:
      direction, entry, stop_loss, tp1, tp2, tp3,
      confidence, reason, gap_atr_ratio, atr_value
    """
    if len(df) < lookback + 3:
        return []

    roll_high = df["high"].rolling(lookback, min_periods=lookback).max().shift(1)
    roll_low = df["low"].rolling(lookback, min_periods=lookback).min().shift(1)

    signals: List[Dict] = []

    # ── SELL: price breaks above swing high, closes back below within 2 bars ──
    for offset in range(-3, 0):
        i = len(df) + offset
        if i < lookback or i >= len(df) - 1:
            continue

        broke = df["high"].iloc[i] > roll_high.iloc[i]
        if not broke:
            continue

        if i + 2 < len(df):
            reverted = df["close"].iloc[i + 2] < roll_high.iloc[i]
        else:
            reverted = False
        if not reverted:
            continue

        if any(s["direction"] == "sell" for s in signals):
            continue

        entry = df["open"].iloc[i + 1]
        atr = df["atr"].iloc[i] if not pd.isna(df["atr"].iloc[i]) else entry * 0.005

        sl_dist = atr * sl_atr_mult
        sl = entry + sl_dist
        tp1 = entry - atr * tp1_atr_mult
        tp2 = entry - atr * tp2_atr_mult
        tp3 = entry - atr * tp3_atr_mult

        gap = df["high"].iloc[i] - roll_high.iloc[i]
        gap_r = max(0.0, gap / atr) if atr > 0 else 0.0
        confidence = min(50.0 + gap_r * 12.5, 75.0)

        swing_lvl = roll_high.iloc[i]
        reason = (
            f"FB Sell: {symbol} broke {lookback}-bar swing high @ {swing_lvl:.5f} "
            f"but closed back below (gap {gap_r:.1f}x ATR)"
        )

        signals.append({
            "direction": "sell",
            "entry": float(entry),
            "stop_loss": float(sl),
            "tp1": float(tp1),
            "tp2": float(tp2),
            "tp3": float(tp3),
            "confidence": round(confidence, 1),
            "reason": reason,
            "gap_atr_ratio": round(gap_r, 2),
            "atr_value": float(atr),
        })

    # ── BUY: price breaks below swing low, closes back above within 2 bars ──
    for offset in range(-3, 0):
        i = len(df) + offset
        if i < lookback or i >= len(df) - 1:
            continue

        broke = df["low"].iloc[i] < roll_low.iloc[i]
        if not broke:
            continue

        if i + 2 < len(df):
            reverted = df["close"].iloc[i + 2] > roll_low.iloc[i]
        else:
            reverted = False
        if not reverted:
            continue

        if any(s["direction"] == "buy" for s in signals):
            continue

        entry = df["open"].iloc[i + 1]
        atr = df["atr"].iloc[i] if not pd.isna(df["atr"].iloc[i]) else entry * 0.005

        sl_dist = atr * sl_atr_mult
        sl = entry - sl_dist
        tp1 = entry + atr * tp1_atr_mult
        tp2 = entry + atr * tp2_atr_mult
        tp3 = entry + atr * tp3_atr_mult

        gap = roll_low.iloc[i] - df["low"].iloc[i]
        gap_r = max(0.0, gap / atr) if atr > 0 else 0.0
        confidence = min(50.0 + gap_r * 12.5, 75.0)

        swing_lvl = roll_low.iloc[i]
        reason = (
            f"FB Buy: {symbol} broke {lookback}-bar swing low @ {swing_lvl:.5f} "
            f"but closed back above (gap {gap_r:.1f}x ATR)"
        )

        signals.append({
            "direction": "buy",
            "entry": float(entry),
            "stop_loss": float(sl),
            "tp1": float(tp1),
            "tp2": float(tp2),
            "tp3": float(tp3),
            "confidence": round(confidence, 1),
            "reason": reason,
            "gap_atr_ratio": round(gap_r, 2),
            "atr_value": float(atr),
        })

    return signals


def pick_best_signal(signals: List[Dict]) -> Optional[Dict]:
    """Return the highest-confidence FB signal (usually at most 1 anyway)."""
    if not signals:
        return None
    return max(signals, key=lambda s: s["confidence"])


def backtest_symbol(
    df: pd.DataFrame,
    symbol: str,
    lookback: int = 10,
    rr: float = 1.5,
    max_hold: int = 24,
) -> List[Dict]:
    """
    Run FB backtest on full DataFrame.
    Returns list of trade result dicts for analysis.
    Adapted from the adversarial test logic.
    """
    trades: List[Dict] = []

    roll_h = df["high"].rolling(lookback, min_periods=lookback).max().shift(1)
    roll_l = df["low"].rolling(lookback, min_periods=lookback).min().shift(1)

    sig = pd.Series(0, index=df.index)
    broke_h = df["high"] > roll_h
    close_below = df["close"].shift(-2) < roll_h
    sig[broke_h & close_below] = -1

    broke_l = df["low"] < roll_l
    close_above = df["close"].shift(-2) > roll_l
    sig[broke_l & close_above] = 1

    min_start = lookback + 5
    for i in range(min_start, len(df) - 1):
        if sig.iloc[i] == 0:
            continue

        ts = df.index[i]
        entry = float(df["open"].iloc[i + 1])
        direction = "buy" if sig.iloc[i] == 1 else "sell"
        atr = float(df["atr"].iloc[i]) if not pd.isna(df["atr"].iloc[i]) else entry * 0.005

        sl_dist = atr * 1.5
        tp_dist = sl_dist * rr

        if direction == "buy":
            sl = entry - sl_dist
            tp = entry + tp_dist
        else:
            sl = entry + sl_dist
            tp = entry - tp_dist

        risk = abs(entry - sl)
        exit_price = entry
        exit_reason = "CLOSE_EXIT"

        for j in range(i + 2, min(i + 2 + max_hold, len(df))):
            c = df.iloc[j]
            if direction == "buy":
                if c["low"] <= sl:
                    exit_price = float(sl)
                    exit_reason = "SL"
                    break
                if c["high"] >= tp:
                    exit_price = float(tp)
                    exit_reason = "TP"
                    break
            else:
                if c["high"] >= sl:
                    exit_price = float(sl)
                    exit_reason = "SL"
                    break
                if c["low"] <= tp:
                    exit_price = float(tp)
                    exit_reason = "TP"
                    break
            exit_price = float(c["close"])
            exit_reason = "TIME_EXIT"

        pnl_raw = (exit_price - entry) if direction == "buy" else (entry - exit_price)
        pnl_r = pnl_raw / risk if risk > 0 else 0

        trades.append({
            "symbol": symbol,
            "entry_date": str(ts.date()),
            "entry_time": str(ts),
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "pnl_r": round(pnl_r, 4),
            "year": ts.year,
        })

    return trades
