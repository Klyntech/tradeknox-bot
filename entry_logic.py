"""
Layer 3: Smart Entry Logic
Order Blocks, Fair Value Gaps, Fibonacci zones, candle confirmation.
Every entry must have a reason — not just 'price is there'.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OrderBlock:
    kind: str           # "bullish" or "bearish"
    top: float
    bottom: float
    origin_index: int
    mitigated: bool     # True if price already entered and reacted
    strength: float     # 1.0 - 3.0 based on move away from OB
    timestamp: object


@dataclass
class FairValueGap:
    kind: str           # "bullish" or "bearish"
    top: float
    bottom: float
    origin_index: int
    filled: bool        # True if price fully closed the gap
    timestamp: object


@dataclass
class FibZone:
    level: float
    ratio: float        # 0.5, 0.618, 0.786
    kind: str           # "support" or "resistance"


@dataclass
class EntrySetup:
    direction: str              # "buy" or "sell"
    entry_price: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    rr_tp1: float
    rr_tp2: float
    rr_tp3: float
    order_block: Optional[OrderBlock]
    fvg: Optional[FairValueGap]
    fib_confluence: bool
    candle_confirmed: bool
    confirmation_type: str      # "engulfing" | "rejection" | "none"
    reason: str                 # human-readable explanation
    atr_fallback: bool = False  # True if no OB/FVG found, used ATR-based entry


def detect_order_blocks(df: pd.DataFrame, lookback: int = 20, atr: float = 1.0) -> List[OrderBlock]:
    """
    A valid Order Block is the LAST opposing candle before a significant impulse move.

    Bullish OB: last bearish candle before a strong bullish impulse (break of structure)
    Bearish OB: last bullish candle before a strong bearish impulse

    Validation: the move away from the OB must be ≥ 2× ATR (not every candle!)
    """
    blocks = []
    n = len(df)
    min_move = atr * 2.0

    for i in range(1, min(lookback, n - 3)):
        idx = n - 1 - i
        candle = df.iloc[idx]
        body_size = abs(candle["close"] - candle["open"])

        # Skip doji/tiny candles
        if body_size < atr * 0.1:
            continue

        # Measure the impulse move AFTER this candle
        future = df.iloc[idx + 1: idx + 6]
        if future.empty:
            continue

        bearish_body = candle["open"] > candle["close"]
        bullish_body = candle["close"] > candle["open"]

        # Bullish OB: bearish candle → strong bullish move after
        if bearish_body:
            impulse = future["high"].max() - candle["low"]
            if impulse >= min_move:
                already_mitigated = df["close"].iloc[idx + 1:].min() < candle["low"]
                strength = min(3.0, impulse / atr)
                blocks.append(OrderBlock(
                    kind="bullish",
                    top=candle["open"],
                    bottom=candle["low"],
                    origin_index=idx,
                    mitigated=already_mitigated,
                    strength=round(strength, 2),
                    timestamp=df.index[idx]
                ))

        # Bearish OB: bullish candle → strong bearish move after
        elif bullish_body:
            impulse = candle["high"] - future["low"].min()
            if impulse >= min_move:
                already_mitigated = df["close"].iloc[idx + 1:].max() > candle["high"]
                strength = min(3.0, impulse / atr)
                blocks.append(OrderBlock(
                    kind="bearish",
                    top=candle["high"],
                    bottom=candle["open"],
                    origin_index=idx,
                    mitigated=already_mitigated,
                    strength=round(strength, 2),
                    timestamp=df.index[idx]
                ))

    return blocks


def detect_fvg(df: pd.DataFrame, atr: float = 1.0, min_atr_size: float = 0.3) -> List[FairValueGap]:
    """
    Fair Value Gap = 3-candle pattern where candle[1]'s range doesn't overlap
    candle[0]'s high and candle[2]'s low (bullish) or vice versa (bearish).

    Min size filter: gap must be ≥ min_atr_size × ATR to avoid noise.
    """
    gaps = []
    n = len(df)
    min_size = atr * min_atr_size

    for i in range(2, n):
        c0 = df.iloc[i - 2]
        c2 = df.iloc[i]

        # Bullish FVG: gap between c0.high and c2.low (price moved up fast)
        if c0["high"] < c2["low"]:
            gap_size = c2["low"] - c0["high"]
            if gap_size >= min_size:
                filled = df["low"].iloc[i + 1:].min() <= c0["high"] if i + 1 < n else False
                gaps.append(FairValueGap(
                    kind="bullish",
                    top=c2["low"],
                    bottom=c0["high"],
                    origin_index=i,
                    filled=filled,
                    timestamp=df.index[i]
                ))

        # Bearish FVG: gap between c0.low and c2.high (price moved down fast)
        elif c0["low"] > c2["high"]:
            gap_size = c0["low"] - c2["high"]
            if gap_size >= min_size:
                filled = df["high"].iloc[i + 1:].max() >= c0["low"] if i + 1 < n else False
                gaps.append(FairValueGap(
                    kind="bearish",
                    top=c0["low"],
                    bottom=c2["high"],
                    origin_index=i,
                    filled=filled,
                    timestamp=df.index[i]
                ))

    return gaps[-20:]  # Return most recent 20 gaps


def compute_fibonacci_zones(swing_high: float, swing_low: float,
                             fib_levels: List[float]) -> List[FibZone]:
    """
    Fibonacci retracement zones between the most recent swing high and low.
    For bullish context: zones are support levels (price retracing down).
    For bearish context: zones are resistance levels (price retracing up).
    """
    zones = []
    rng = swing_high - swing_low

    for ratio in fib_levels:
        # Retracement from high
        support_level = swing_high - rng * ratio
        zones.append(FibZone(level=round(support_level, 5), ratio=ratio, kind="support"))

    return zones


def price_in_zone(price: float, top: float, bottom: float, buffer_pct: float = 0.001) -> bool:
    """Check if price is within a zone, with a small buffer."""
    buf = (top - bottom) * buffer_pct + top * 0.0001
    return (bottom - buf) <= price <= (top + buf)


def detect_candle_confirmation(df: pd.DataFrame, direction: str) -> Tuple[bool, str]:
    """
    Look at the last 3 candles for confirmation patterns.
    - Engulfing: current candle body fully engulfs previous
    - Rejection: long wick (≥ 2× body) in the opposite direction (pin bar)
    - Momentum: 2+ consecutive closes in the signal direction
    """
    if len(df) < 3:
        return False, "none"

    c1 = df.iloc[-2]   # previous candle
    c0 = df.iloc[-1]   # current (last complete) candle

    body0 = abs(c0["close"] - c0["open"])
    body1 = abs(c1["close"] - c1["open"])
    upper_wick = c0["high"] - max(c0["close"], c0["open"])
    lower_wick = min(c0["close"], c0["open"]) - c0["low"]

    if direction == "buy":
        # Bullish engulfing
        if (c0["close"] > c0["open"] and        # green candle
                c0["open"] < c1["close"] and
                c0["close"] > c1["open"] and
                body0 > body1):
            return True, "engulfing"

        # Bullish pin bar (rejection of lows)
        if body0 > 0 and lower_wick >= body0 * 2:
            return True, "rejection"

    elif direction == "sell":
        # Bearish engulfing
        if (c0["close"] < c0["open"] and        # red candle
                c0["open"] > c1["close"] and
                c0["close"] < c1["open"] and
                body0 > body1):
            return True, "engulfing"

        # Bearish pin bar (rejection of highs)
        if body0 > 0 and upper_wick >= body0 * 2:
            return True, "rejection"

    return False, "none"


def find_best_entry(df: pd.DataFrame,
                    direction: str,
                    structure,
                    config) -> Optional[EntrySetup]:
    """
    Assemble the best entry setup given direction and market structure.
    Returns None if no valid setup exists.
    """
    current_price = df["close"].iloc[-1]
    atr = df["atr"].iloc[-1]

    # Detect all entry components
    obs = detect_order_blocks(df, lookback=config.OB_LOOKBACK, atr=atr)
    fvgs = detect_fvg(df, atr=atr, min_atr_size=config.FVG_MIN_SIZE_ATR)

    # Fibonacci — use last swing to current swing
    swing_highs = structure.swing_highs
    swing_lows = structure.swing_lows

    fib_zones = []
    if swing_highs and swing_lows:
        sh = swing_highs[-1].price
        sl = swing_lows[-1].price
        fib_zones = compute_fibonacci_zones(sh, sl, config.FIB_LEVELS)

    # Find matching Order Block
    matching_ob = None
    for ob in sorted(obs, key=lambda x: -x.strength):
        if ob.kind == direction and not ob.mitigated:
            if price_in_zone(current_price, ob.top, ob.bottom, buffer_pct=0.002):
                matching_ob = ob
                break

    # Find matching FVG
    matching_fvg = None
    fvg_kind = "bullish" if direction == "buy" else "bearish"
    for gap in reversed(fvgs):
        if gap.kind == fvg_kind and not gap.filled:
            if price_in_zone(current_price, gap.top, gap.bottom, buffer_pct=0.002):
                matching_fvg = gap
                break

    # Check Fibonacci confluence
    fib_confluence = any(
        abs(current_price - z.level) / current_price < 0.002
        for z in fib_zones
    )

    # Candle confirmation
    confirmed, conf_type = detect_candle_confirmation(df, direction)

    # ── Structure alignment check ──────────────────────────────────────────
    # Don't buy at the top (premium) or sell at the bottom (discount)
    if direction == "buy" and structure.current_price_zone == "premium":
        return None
    if direction == "sell" and structure.current_price_zone == "discount":
        return None

    # ── ATR-based fallback if no OB or FVG found ─────────────────────────────
    atr_fallback = False
    if matching_ob is None and matching_fvg is None:
        # Only allow fallback if price is in a valid zone (discount for buy, premium for sell)
        if direction == "buy" and structure.current_price_zone == "discount":
            atr_fallback = True
        elif direction == "sell" and structure.current_price_zone == "premium":
            atr_fallback = True
        else:
            return None

    # ── Calculate SL and TP levels ──────────────────────────────────────────
    if direction == "buy":
        # SL below the OB or ATR-based, whichever is tighter
        if matching_ob:
            sl_price = matching_ob.bottom - atr * 0.3
        else:
            sl_price = current_price - atr * config.ATR_SL_MULTIPLIER

        risk = current_price - sl_price
        tp1 = current_price + risk * config.TP1_ATR_MULT
        tp2 = current_price + risk * config.TP2_ATR_MULT
        tp3 = current_price + risk * config.TP3_ATR_MULT
        entry = current_price

    else:  # sell
        if matching_ob:
            sl_price = matching_ob.top + atr * 0.3
        else:
            sl_price = current_price + atr * config.ATR_SL_MULTIPLIER

        risk = sl_price - current_price
        tp1 = current_price - risk * config.TP1_ATR_MULT
        tp2 = current_price - risk * config.TP2_ATR_MULT
        tp3 = current_price - risk * config.TP3_ATR_MULT
        entry = current_price

    if risk <= 0:
        return None

    rr1 = round(abs(tp1 - entry) / risk, 2)
    rr2 = round(abs(tp2 - entry) / risk, 2)
    rr3 = round(abs(tp3 - entry) / risk, 2)

    if rr1 < config.MIN_RR_RATIO:
        return None

    # ── Build reason string ──────────────────────────────────────────────────
    reasons = []
    if matching_ob:
        reasons.append(f"{direction.capitalize()} OB (strength {matching_ob.strength}×)")
    if matching_fvg:
        reasons.append(f"{fvg_kind.capitalize()} FVG at {matching_fvg.bottom:.2f}–{matching_fvg.top:.2f}")
    if atr_fallback:
        reasons.append(f"ATR-based entry ({structure.current_price_zone} zone)")
    if fib_confluence:
        reasons.append("Fib confluence")
    if confirmed:
        reasons.append(f"{conf_type.capitalize()} candle confirm")
    if structure.last_bos and structure.last_bos.direction == ("bullish" if direction == "buy" else "bearish"):
        reasons.append("BOS confirmed")
    if structure.last_choch and structure.last_choch.direction == ("bullish" if direction == "buy" else "bearish"):
        reasons.append("CHoCH confirmed")

    reason_str = ", ".join(reasons) if reasons else "Entry zone"

    return EntrySetup(
        direction=direction,
        entry_price=round(entry, 5),
        stop_loss=round(sl_price, 5),
        tp1=round(tp1, 5),
        tp2=round(tp2, 5),
        tp3=round(tp3, 5),
        rr_tp1=rr1,
        rr_tp2=rr2,
        rr_tp3=rr3,
        order_block=matching_ob,
        fvg=matching_fvg,
        fib_confluence=fib_confluence,
        candle_confirmed=confirmed,
        confirmation_type=conf_type,
        reason=reason_str,
        atr_fallback=atr_fallback
    )
