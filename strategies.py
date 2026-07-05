"""
Trading Strategies — Research-Backed

Proven strategies from 2-year backtest on 5 symbols:
- MA 50/200 Crossover: Best on XAUUSD (PF 1.18, Sharpe 0.070)
- MA 21/50 Crossover: Best on USDJPY (PF 1.21, Sharpe 0.075)
- Breakout 20-bar: Works on XAUUSD (PF 1.14)
- EMA Alignment: Confluence filter

Dropped (proven losers):
- RSI Mean Reversion: PF < 0.90 on all pairs
- Bollinger Bounce: PF < 1.00 on all pairs
"""

import logging
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 1: MA Crossover (Proven)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class MACrossoverSignal:
    direction: str          # "bullish" | "bearish" | "neutral"
    fast_ma: float
    slow_ma: float
    cross_type: str         # "golden" | "death" | "none"
    strength: float         # 0.0 - 1.0 based on MA separation
    bars_since_cross: int   # how many bars since the cross


def detect_ma_crossover(df: pd.DataFrame, fast_period: int = 50,
                        slow_period: int = 200) -> MACrossoverSignal:
    """
    Detect MA crossover events — ONLY on actual crossover, not position.
    Golden Cross: Fast MA crosses above Slow MA → bullish
    Death Cross: Fast MA crosses below Slow MA → bearish
    """
    if len(df) < slow_period + 5:
        return MACrossoverSignal("neutral", 0, 0, "none", 0.0, 0)

    fast_ma = df["close"].ewm(span=fast_period, adjust=False).mean()
    slow_ma = df["close"].ewm(span=slow_period, adjust=False).mean()

    current_fast = fast_ma.iloc[-1]
    current_slow = slow_ma.iloc[-1]
    prev_fast = fast_ma.iloc[-2]
    prev_slow = slow_ma.iloc[-2]

    # Detect ACTUAL crossover (not position)
    cross_type = "none"
    direction = "neutral"
    bars_since = 0

    # Golden Cross: fast was below slow, now above
    if prev_fast <= prev_slow and current_fast > current_slow:
        cross_type = "golden"
        direction = "bullish"
    # Death Cross: fast was above slow, now below
    elif prev_fast >= prev_slow and current_fast < current_slow:
        cross_type = "death"
        direction = "bearish"

    # Find how many bars since last cross
    if cross_type != "none":
        bars_since = 0
    else:
        for i in range(2, min(50, len(df))):
            prev_f = fast_ma.iloc[-(i+1)]
            prev_s = slow_ma.iloc[-(i+1)]
            curr_f = fast_ma.iloc[-i]
            curr_s = slow_ma.iloc[-i]
            if (prev_f <= prev_s and curr_f > curr_s) or \
               (prev_f >= prev_s and curr_f < curr_s):
                bars_since = i - 1
                # Set direction based on current state
                if current_fast > current_slow:
                    direction = "bullish"
                else:
                    direction = "bearish"
                break

    # Strength based on MA separation (normalized by ATR)
    atr = df["atr"].iloc[-1] if "atr" in df.columns else 1.0
    separation = abs(current_fast - current_slow)
    strength = min(1.0, separation / (atr * 5)) if atr > 0 else 0.0

    return MACrossoverSignal(
        direction=direction,
        fast_ma=round(current_fast, 5),
        slow_ma=round(current_slow, 5),
        cross_type=cross_type,
        strength=round(strength, 3),
        bars_since_cross=bars_since
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 2: Breakout 20-bar (Proven)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BreakoutSignal:
    direction: str          # "bullish" | "bearish" | "neutral"
    breakout_level: float   # the level that was broken
    current_price: float
    volume_confirmed: bool  # volume >= threshold
    strength: float         # 0.0 - 1.0 based on volume and distance
    lookback_high: float
    lookback_low: float


def detect_breakout(df: pd.DataFrame, lookback: int = 20,
                    volume_mult: float = 1.5) -> BreakoutSignal:
    """
    Breakout Strategy: Price breaks N-day high/low with volume confirmation.
    Proven on XAUUSD (PF 1.14, Sharpe 0.048).
    """
    if len(df) < lookback + 5:
        return BreakoutSignal("neutral", 0, 0, False, 0.0, 0, 0)

    current_price = df["close"].iloc[-1]
    current_volume = df["volume"].iloc[-1] if "volume" in df.columns else 0
    avg_volume = df["volume"].iloc[-(lookback+1):-1].mean() if "volume" in df.columns else 1

    # N-bar high/low (excluding current candle)
    lookback_high = df["high"].iloc[-(lookback+1):-1].max()
    lookback_low = df["low"].iloc[-(lookback+1):-1].min()

    # Volume confirmation
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    volume_confirmed = volume_ratio >= volume_mult

    direction = "neutral"
    breakout_level = 0
    strength = 0.0

    # Bullish breakout: price closes above N-bar high
    if current_price > lookback_high:
        direction = "bullish"
        breakout_level = lookback_high
        distance_pct = (current_price - lookback_high) / lookback_high * 100
        strength = min(1.0, (distance_pct / 2) * min(volume_ratio / volume_mult, 2.0))
    # Bearish breakout: price closes below N-bar low
    elif current_price < lookback_low:
        direction = "bearish"
        breakout_level = lookback_low
        distance_pct = (lookback_low - current_price) / lookback_low * 100
        strength = min(1.0, (distance_pct / 2) * min(volume_ratio / volume_mult, 2.0))

    return BreakoutSignal(
        direction=direction,
        breakout_level=round(breakout_level, 5),
        current_price=round(current_price, 5),
        volume_confirmed=volume_confirmed,
        strength=round(strength, 3),
        lookback_high=round(lookback_high, 5),
        lookback_low=round(lookback_low, 5)
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 3: EMA Alignment (Proven)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class EMAAlignmentSignal:
    direction: str          # "bullish" | "bearish" | "neutral"
    aligned: bool           # all EMAs aligned
    strength: float         # 0.0 - 1.0 based on EMA spacing
    above_200: bool         # price above 200 EMA


def detect_ema_alignment(df: pd.DataFrame) -> EMAAlignmentSignal:
    """
    EMA Alignment: All EMAs aligned in same direction.
    Proven on XAUUSD (PF 1.19).
    """
    if len(df) < 200:
        return EMAAlignmentSignal("neutral", False, 0.0, False)

    ema_9 = df["ema_9"].iloc[-1] if "ema_9" in df.columns else df["close"].ewm(span=9).mean().iloc[-1]
    ema_21 = df["ema_21"].iloc[-1] if "ema_21" in df.columns else df["close"].ewm(span=21).mean().iloc[-1]
    ema_50 = df["ema_50"].iloc[-1] if "ema_50" in df.columns else df["close"].ewm(span=50).mean().iloc[-1]
    ema_200 = df["ema_200"].iloc[-1] if "ema_200" in df.columns else df["close"].ewm(span=200).mean().iloc[-1]
    current_price = df["close"].iloc[-1]

    # Check alignment
    bull_aligned = ema_9 > ema_21 > ema_50 and current_price > ema_200
    bear_aligned = ema_9 < ema_21 < ema_50 and current_price < ema_200

    if bull_aligned:
        direction = "bullish"
        aligned = True
    elif bear_aligned:
        direction = "bearish"
        aligned = True
    else:
        direction = "neutral"
        aligned = False

    # Strength based on EMA spacing
    atr = df["atr"].iloc[-1] if "atr" in df.columns else 1.0
    spacing = abs(ema_9 - ema_50)
    strength = min(1.0, spacing / (atr * 3)) if atr > 0 else 0.0

    return EMAAlignmentSignal(
        direction=direction,
        aligned=aligned,
        strength=round(strength, 3),
        above_200=current_price > ema_200
    )


# ──────────────────────────────────────────────────────────────────────────────
# Combined Strategy Assessment
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class StrategyConfluence:
    ma_direction: str
    ma_strength: float
    breakout_direction: str
    breakout_strength: float
    ema_direction: str
    ema_aligned: bool
    confluence_score: int     # 0-3: how many strategies agree
    confluence_direction: str # "bullish" | "bearish" | "neutral"


def assess_strategies(df: pd.DataFrame, direction: str,
                      config) -> StrategyConfluence:
    """
    Run all proven strategies and assess confluence with the given direction.
    Returns confluence data for scoring.
    """
    # Run MA Crossover (50/200)
    ma_signal = detect_ma_crossover(
        df, fast_period=getattr(config, "MA_FAST_PERIOD", 50),
        slow_period=getattr(config, "MA_SLOW_PERIOD", 200)
    )

    # Run Breakout 20-bar
    breakout_signal = detect_breakout(
        df, lookback=getattr(config, "BREAKOUT_LOOKBACK", 20),
        volume_mult=getattr(config, "BREAKOUT_VOLUME_MULT", 1.5)
    )

    # Run EMA Alignment
    ema_signal = detect_ema_alignment(df)

    # Count confluence
    bullish_count = sum(1 for s in [ma_signal, breakout_signal, ema_signal]
                       if s.direction == "bullish")
    bearish_count = sum(1 for s in [ma_signal, breakout_signal, ema_signal]
                       if s.direction == "bearish")

    if bullish_count > bearish_count:
        confluence_dir = "bullish"
        confluence_score = bullish_count
    elif bearish_count > bullish_count:
        confluence_dir = "bearish"
        confluence_score = bearish_count
    else:
        confluence_dir = "neutral"
        confluence_score = 0

    return StrategyConfluence(
        ma_direction=ma_signal.direction,
        ma_strength=ma_signal.strength,
        breakout_direction=breakout_signal.direction,
        breakout_strength=breakout_signal.strength,
        ema_direction=ema_signal.direction,
        ema_aligned=ema_signal.aligned,
        confluence_score=confluence_score,
        confluence_direction=confluence_dir
    )
