"""
Layer 2: Market Structure Engine
Trend detection, CHoCH & BOS, liquidity zones, premium/discount areas.
This is the brain — structure-first, indicators second.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class Trend(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGING = "ranging"


@dataclass
class SwingPoint:
    index: int
    price: float
    kind: str          # "high" or "low"
    timestamp: object


@dataclass
class StructureBreak:
    kind: str          # "BOS" or "CHoCH"
    direction: str     # "bullish" or "bearish"
    level: float
    candle_index: int
    confirmed: bool


@dataclass
class LiquidityZone:
    level: float
    kind: str          # "equal_highs" | "equal_lows" | "swing_high" | "swing_low"
    strength: int      # number of touches
    swept: bool        # True if price already ran through it


@dataclass
class MarketStructure:
    trend: Trend
    last_bos: Optional[StructureBreak]
    last_choch: Optional[StructureBreak]
    liquidity_zones: List[LiquidityZone]
    premium_zone: Tuple[float, float]   # (low, high) of premium area
    discount_zone: Tuple[float, float]  # (low, high) of discount area
    equilibrium: float                  # 50% of range
    current_price_zone: str            # "premium" | "discount" | "equilibrium"
    swing_highs: List[SwingPoint]
    swing_lows: List[SwingPoint]


def detect_swing_points(df: pd.DataFrame, lookback: int = 5) -> Tuple[List[SwingPoint], List[SwingPoint]]:
    """
    Identify significant swing highs and lows using a rolling window.
    A swing high: candle[i].high is the highest in [i-lookback : i+lookback]
    """
    highs, lows = [], []
    n = len(df)

    for i in range(lookback, n - lookback):
        window_h = df["high"].iloc[i - lookback: i + lookback + 1]
        window_l = df["low"].iloc[i - lookback: i + lookback + 1]

        if df["high"].iloc[i] == window_h.max():
            highs.append(SwingPoint(
                index=i,
                price=df["high"].iloc[i],
                kind="high",
                timestamp=df.index[i]
            ))

        if df["low"].iloc[i] == window_l.min():
            lows.append(SwingPoint(
                index=i,
                price=df["low"].iloc[i],
                kind="low",
                timestamp=df.index[i]
            ))

    return highs, lows


def detect_trend(swing_highs: List[SwingPoint], swing_lows: List[SwingPoint]) -> Trend:
    """
    Trend = Higher Highs + Higher Lows → Bullish
           Lower Highs + Lower Lows  → Bearish
           Mixed                     → Ranging
    """
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return Trend.RANGING

    hh = swing_highs[-1].price > swing_highs[-2].price
    lh = swing_highs[-1].price < swing_highs[-2].price
    hl = swing_lows[-1].price > swing_lows[-2].price
    ll = swing_lows[-1].price < swing_lows[-2].price

    if hh and hl:
        return Trend.BULLISH
    if lh and ll:
        return Trend.BEARISH
    return Trend.RANGING


def detect_structure_breaks(df: pd.DataFrame,
                             swing_highs: List[SwingPoint],
                             swing_lows: List[SwingPoint]) -> List[StructureBreak]:
    """
    BOS  (Break of Structure)  — price breaks in the direction of trend.
         Bullish: closes above prev swing high.
         Bearish: closes below prev swing low.
    CHoCH (Change of Character) — price breaks AGAINST the trend.
         Bullish CHoCH: in a bearish trend, price closes above a swing high.
         Bearish CHoCH: in a bullish trend, price closes below a swing low.
    """
    breaks = []
    closes = df["close"]
    current_trend = detect_trend(swing_highs, swing_lows)

    # Check last N swing points for breaks
    for sh in swing_highs[-5:]:
        # Find first candle after this swing that closes above it
        after = closes.iloc[sh.index + 1:]
        break_candles = after[after > sh.price]
        if not break_candles.empty:
            idx = df.index.get_loc(break_candles.index[0])
            kind = "BOS" if current_trend == Trend.BULLISH else "CHoCH"
            breaks.append(StructureBreak(
                kind=kind,
                direction="bullish",
                level=sh.price,
                candle_index=idx,
                confirmed=True
            ))

    for sl in swing_lows[-5:]:
        after = closes.iloc[sl.index + 1:]
        break_candles = after[after < sl.price]
        if not break_candles.empty:
            idx = df.index.get_loc(break_candles.index[0])
            kind = "BOS" if current_trend == Trend.BEARISH else "CHoCH"
            breaks.append(StructureBreak(
                kind=kind,
                direction="bearish",
                level=sl.price,
                candle_index=idx,
                confirmed=True
            ))

    # Sort by candle_index, return most recent first
    breaks.sort(key=lambda b: b.candle_index, reverse=True)
    return breaks


def detect_liquidity_zones(swing_highs: List[SwingPoint],
                            swing_lows: List[SwingPoint],
                            current_price: float,
                            atr: float,
                            tolerance_pct: float = 0.001) -> List[LiquidityZone]:
    """
    Liquidity pools sit above swing highs and below swing lows.
    Equal highs/lows = multiple swings within tolerance of each other.
    """
    zones = []
    tol = current_price * tolerance_pct

    # Group swing highs within tolerance (equal highs = liquidity pool)
    for i, sh in enumerate(swing_highs):
        cluster = [s for s in swing_highs if abs(s.price - sh.price) <= tol]
        if len(cluster) >= 2:
            avg = np.mean([s.price for s in cluster])
            swept = current_price > avg + atr * 0.5
            zones.append(LiquidityZone(
                level=round(avg, 5),
                kind="equal_highs",
                strength=len(cluster),
                swept=swept
            ))
        else:
            swept = current_price > sh.price + atr * 0.5
            zones.append(LiquidityZone(
                level=sh.price,
                kind="swing_high",
                strength=1,
                swept=swept
            ))

    for sl in swing_lows:
        cluster = [s for s in swing_lows if abs(s.price - sl.price) <= tol]
        if len(cluster) >= 2:
            avg = np.mean([s.price for s in cluster])
            swept = current_price < avg - atr * 0.5
            zones.append(LiquidityZone(
                level=round(avg, 5),
                kind="equal_lows",
                strength=len(cluster),
                swept=swept
            ))
        else:
            swept = current_price < sl.price - atr * 0.5
            zones.append(LiquidityZone(
                level=sl.price,
                kind="swing_low",
                strength=1,
                swept=swept
            ))

    # Deduplicate and sort
    seen = set()
    unique = []
    for z in zones:
        key = round(z.level, 3)
        if key not in seen:
            seen.add(key)
            unique.append(z)

    return unique


def detect_premium_discount(swing_highs: List[SwingPoint],
                             swing_lows: List[SwingPoint],
                             current_price: float) -> Tuple[Tuple, Tuple, float, str]:
    """
    Premium  = upper 50% of the most recent range (sell zone)
    Discount = lower 50% of the most recent range (buy zone)
    Equilibrium = 50% level
    """
    if not swing_highs or not swing_lows:
        return (current_price, current_price), (current_price, current_price), current_price, "equilibrium"

    recent_high = max(sh.price for sh in swing_highs[-3:]) if len(swing_highs) >= 1 else swing_highs[-1].price
    recent_low = min(sl.price for sl in swing_lows[-3:]) if len(swing_lows) >= 1 else swing_lows[-1].price

    equil = (recent_high + recent_low) / 2
    premium_zone = (equil, recent_high)
    discount_zone = (recent_low, equil)

    if current_price >= equil:
        zone = "premium"
    else:
        zone = "discount"

    return premium_zone, discount_zone, equil, zone


def analyze_market_structure(df: pd.DataFrame, config) -> MarketStructure:
    """
    Full market structure analysis. Returns a MarketStructure object.
    This is the entry point for Layer 2.
    """
    swing_highs, swing_lows = detect_swing_points(df, lookback=5)

    if not swing_highs or not swing_lows:
        logger.warning("Not enough swing points detected — insufficient data?")

    trend = detect_trend(swing_highs, swing_lows)
    breaks = detect_structure_breaks(df, swing_highs, swing_lows)

    last_bos = next((b for b in breaks if b.kind == "BOS"), None)
    last_choch = next((b for b in breaks if b.kind == "CHoCH"), None)

    current_price = df["close"].iloc[-1]
    atr = df["atr"].iloc[-1] if "atr" in df.columns else 1.0

    liquidity = detect_liquidity_zones(swing_highs, swing_lows, current_price, atr)
    premium, discount, equil, price_zone = detect_premium_discount(
        swing_highs, swing_lows, current_price
    )

    return MarketStructure(
        trend=trend,
        last_bos=last_bos,
        last_choch=last_choch,
        liquidity_zones=liquidity,
        premium_zone=premium,
        discount_zone=discount,
        equilibrium=equil,
        current_price_zone=price_zone,
        swing_highs=swing_highs[-10:],
        swing_lows=swing_lows[-10:],
    )
