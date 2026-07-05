"""
Trading Strategies — Research-Backed (Multi-Timeframe)

Best strategies per pair from 2-year backtest across 4 timeframes:

XAUUSD 4h:
  - Breakout 10: WR 47.7%, PF 1.37, Sharpe 0.154
  - Breakout 20: WR 47.8%, PF 1.37, Sharpe 0.156
  - MA 9/21: WR 48.5%, PF 1.41, Sharpe 0.170

EURUSD 15m:
  - MA 21/50: WR 51.8%, PF 1.61, Sharpe 0.236
  - MA 50/200: WR 51.4%, PF 1.58, Sharpe 0.227

GBPUSD 4h:
  - MA 9/21: WR 49.6%, PF 1.48, Sharpe 0.192

USDJPY 15m/4h:
  - Overlap Session: WR 48.3%, PF 1.40, Sharpe 0.166
  - RSI 20/80: WR 49.8%, PF 1.49, Sharpe 0.196

GBPJPY 4h:
  - RSI 20/80: WR 53.1%, PF 1.70, Sharpe 0.263
  - MA 50/200: WR 50.0%, PF 1.50, Sharpe 0.200
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 1: MA Crossover (ACTUAL crossover detection)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class MACrossoverSignal:
    direction: str          # "bullish" | "bearish" | "neutral"
    fast_ma: float
    slow_ma: float
    cross_type: str         # "golden" | "death" | "none"
    strength: float         # 0.0 - 1.0
    bars_since_cross: int


def detect_ma_crossover(df: pd.DataFrame, fast_period: int = 9,
                        slow_period: int = 21) -> MACrossoverSignal:
    """
    Detect MA crossover events — ONLY on actual crossover, not position.
    """
    if len(df) < slow_period + 5:
        return MACrossoverSignal("neutral", 0, 0, "none", 0.0, 0)

    fast_ma = df["close"].ewm(span=fast_period, adjust=False).mean()
    slow_ma = df["close"].ewm(span=slow_period, adjust=False).mean()

    current_fast = fast_ma.iloc[-1]
    current_slow = slow_ma.iloc[-1]
    prev_fast = fast_ma.iloc[-2]
    prev_slow = slow_ma.iloc[-2]

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
                if current_fast > current_slow:
                    direction = "bullish"
                else:
                    direction = "bearish"
                break

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
# Strategy 2: Breakout (N-bar high/low)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BreakoutSignal:
    direction: str
    breakout_level: float
    current_price: float
    strength: float
    lookback_high: float
    lookback_low: float


def detect_breakout(df: pd.DataFrame, lookback: int = 10) -> BreakoutSignal:
    """
    Breakout Strategy: Price breaks N-bar high/low.
    Best on XAUUSD 4h (PF 1.37, Sharpe 0.15+).
    """
    if len(df) < lookback + 5:
        return BreakoutSignal("neutral", 0, 0, 0.0, 0, 0)

    current_price = df["close"].iloc[-1]
    lookback_high = df["high"].iloc[-(lookback+1):-1].max()
    lookback_low = df["low"].iloc[-(lookback+1):-1].min()

    direction = "neutral"
    breakout_level = 0
    strength = 0.0

    if current_price > lookback_high:
        direction = "bullish"
        breakout_level = lookback_high
        distance_pct = (current_price - lookback_high) / lookback_high * 100
        strength = min(1.0, distance_pct / 2)
    elif current_price < lookback_low:
        direction = "bearish"
        breakout_level = lookback_low
        distance_pct = (lookback_low - current_price) / lookback_low * 100
        strength = min(1.0, distance_pct / 2)

    return BreakoutSignal(
        direction=direction,
        breakout_level=round(breakout_level, 5),
        current_price=round(current_price, 5),
        strength=round(strength, 3),
        lookback_high=round(lookback_high, 5),
        lookback_low=round(lookback_low, 5)
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 3: RSI Extreme Reversal
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class RSIExtremesSignal:
    direction: str
    rsi_value: float
    level: str              # "oversold" | "overbought" | "neutral"
    strength: float


def detect_rsi_extremes(df: pd.DataFrame, oversold: float = 20,
                        overbought: float = 80) -> RSIExtremesSignal:
    """
    RSI Extreme Reversal: Buy when RSI < oversold, sell when RSI > overbought.
    Best on GBPJPY 4h (WR 53.1%, PF 1.70, Sharpe 0.263).
    """
    if "rsi" not in df.columns or len(df) < 20:
        return RSIExtremesSignal("neutral", 50, "neutral", 0.0)

    rsi = df["rsi"].iloc[-1]
    direction = "neutral"
    level = "neutral"
    strength = 0.0

    if rsi < oversold:
        direction = "bullish"
        level = "oversold"
        strength = min(1.0, (oversold - rsi) / oversold)
    elif rsi > overbought:
        direction = "bearish"
        level = "overbought"
        strength = min(1.0, (rsi - overbought) / (100 - overbought))

    return RSIExtremesSignal(
        direction=direction,
        rsi_value=round(rsi, 1),
        level=level,
        strength=round(strength, 3)
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 4: Session Timing
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SessionSignal:
    direction: str
    session: str
    active: bool
    strength: float


def detect_session_entry(df: pd.DataFrame) -> SessionSignal:
    """
    Session Entry: Best during London-NY overlap.
    Best on USDJPY 15m (WR 48.3%, PF 1.40, Sharpe 0.166).
    """
    if "hour" not in df.columns:
        return SessionSignal("neutral", "unknown", False, 0.0)

    hour = df["hour"].iloc[-1]

    if 12 <= hour < 16:
        return SessionSignal("neutral", "overlap", True, 0.8)
    elif 7 <= hour < 12:
        return SessionSignal("neutral", "london", True, 0.5)
    elif 12 <= hour < 21:
        return SessionSignal("neutral", "new_york", True, 0.5)

    return SessionSignal("neutral", "off_session", False, 0.0)


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 5: EMA Alignment
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class EMAAlignmentSignal:
    direction: str
    aligned: bool
    strength: float
    above_200: bool


def detect_ema_alignment(df: pd.DataFrame) -> EMAAlignmentSignal:
    """
    EMA Alignment: All EMAs aligned in same direction.
    """
    if len(df) < 200:
        return EMAAlignmentSignal("neutral", False, 0.0, False)

    ema_9 = df["ema_9"].iloc[-1] if "ema_9" in df.columns else df["close"].ewm(span=9).mean().iloc[-1]
    ema_21 = df["ema_21"].iloc[-1] if "ema_21" in df.columns else df["close"].ewm(span=21).mean().iloc[-1]
    ema_50 = df["ema_50"].iloc[-1] if "ema_50" in df.columns else df["close"].ewm(span=50).mean().iloc[-1]
    ema_200 = df["ema_200"].iloc[-1] if "ema_200" in df.columns else df["close"].ewm(span=200).mean().iloc[-1]
    current_price = df["close"].iloc[-1]

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
# Combined Strategy Assessment (Per-Pair, Multi-Timeframe)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class StrategyConfluence:
    ma_direction: str
    ma_strength: float
    breakout_direction: str
    breakout_strength: float
    rsi_direction: str
    rsi_strength: float
    session_active: bool
    ema_direction: str
    ema_aligned: bool
    confluence_score: int     # 0-3
    confluence_direction: str


# Per-pair optimal strategy configs
PAIR_STRATEGIES: Dict[str, Dict] = {
    "XAUUSD": {
        "timeframe": "4h",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 10,
        "rsi_oversold": 30, "rsi_overbought": 70,
        "weights": {"breakout": 2, "ma": 1, "ema": 0},  # breakout dominates
    },
    "EURUSD": {
        "timeframe": "15m",
        "ma_fast": 21, "ma_slow": 50,
        "breakout_lookback": 20,
        "rsi_oversold": 25, "rsi_overbought": 75,
        "weights": {"ma": 2, "ema": 1, "breakout": 0},  # MA crossover dominates
    },
    "GBPUSD": {
        "timeframe": "4h",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 20,
        "rsi_oversold": 30, "rsi_overbought": 70,
        "weights": {"ma": 2, "ema": 1, "breakout": 0},  # MA crossover dominates
    },
    "USDJPY": {
        "timeframe": "15m",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 20,
        "rsi_oversold": 20, "rsi_overbought": 80,
        "weights": {"rsi": 2, "session": 1, "ma": 0},  # RSI extremes + session
    },
    "GBPJPY": {
        "timeframe": "4h",
        "ma_fast": 50, "ma_slow": 200,
        "breakout_lookback": 20,
        "rsi_oversold": 20, "rsi_overbought": 80,
        "weights": {"rsi": 2, "ma": 1, "ema": 0},  # RSI extremes dominate
    },
}


def get_pair_config(symbol: str) -> Dict:
    """Get optimal strategy config for a pair."""
    return PAIR_STRATEGIES.get(symbol, PAIR_STRATEGIES["XAUUSD"])


def assess_strategies(df: pd.DataFrame, direction: str,
                      config, symbol: str = "XAUUSD") -> StrategyConfluence:
    """
    Run all proven strategies and assess confluence with the given direction.
    Uses per-pair optimal parameters from research.
    """
    pair_cfg = get_pair_config(symbol)

    # Run MA Crossover (per-pair optimal)
    ma_signal = detect_ma_crossover(
        df, fast_period=pair_cfg["ma_fast"],
        slow_period=pair_cfg["ma_slow"]
    )

    # Run Breakout (per-pair optimal lookback)
    breakout_signal = detect_breakout(
        df, lookback=pair_cfg["breakout_lookback"]
    )

    # Run RSI Extremes (per-pair optimal levels)
    rsi_signal = detect_rsi_extremes(
        df, oversold=pair_cfg["rsi_oversold"],
        overbought=pair_cfg["rsi_overbought"]
    )

    # Run Session
    session_signal = detect_session_entry(df)

    # Run EMA Alignment
    ema_signal = detect_ema_alignment(df)

    # Weighted confluence
    strat_direction = "bullish" if direction == "buy" else "bearish"
    weights = pair_cfg["weights"]

    score = 0
    max_score = 0

    if weights.get("breakout", 0) > 0:
        max_score += weights["breakout"]
        if breakout_signal.direction == strat_direction:
            score += weights["breakout"]

    if weights.get("ma", 0) > 0:
        max_score += weights["ma"]
        if ma_signal.direction == strat_direction:
            score += weights["ma"]

    if weights.get("rsi", 0) > 0:
        max_score += weights["rsi"]
        if rsi_signal.direction == strat_direction:
            score += weights["rsi"]

    if weights.get("session", 0) > 0:
        max_score += weights["session"]
        if session_signal.active:
            score += weights["session"]

    if weights.get("ema", 0) > 0:
        max_score += weights["ema"]
        if ema_signal.direction == strat_direction:
            score += weights["ema"]

    # Normalize to 0-3 range
    if max_score > 0:
        confluence_score = round(score / max_score * 3)
    else:
        confluence_score = 0

    # Determine direction
    bullish_score = 0
    bearish_score = 0

    if breakout_signal.direction == "bullish":
        bullish_score += weights.get("breakout", 0)
    elif breakout_signal.direction == "bearish":
        bearish_score += weights.get("breakout", 0)

    if ma_signal.direction == "bullish":
        bullish_score += weights.get("ma", 0)
    elif ma_signal.direction == "bearish":
        bearish_score += weights.get("ma", 0)

    if rsi_signal.direction == "bullish":
        bullish_score += weights.get("rsi", 0)
    elif rsi_signal.direction == "bearish":
        bearish_score += weights.get("rsi", 0)

    if ema_signal.direction == "bullish":
        bullish_score += weights.get("ema", 0)
    elif ema_signal.direction == "bearish":
        bearish_score += weights.get("ema", 0)

    if bullish_score > bearish_score:
        confluence_dir = "bullish"
    elif bearish_score > bullish_score:
        confluence_dir = "bearish"
    else:
        confluence_dir = "neutral"

    return StrategyConfluence(
        ma_direction=ma_signal.direction,
        ma_strength=ma_signal.strength,
        breakout_direction=breakout_signal.direction,
        breakout_strength=breakout_signal.strength,
        rsi_direction=rsi_signal.direction,
        rsi_strength=rsi_signal.strength,
        session_active=session_signal.active,
        ema_direction=ema_signal.direction,
        ema_aligned=ema_signal.aligned,
        confluence_score=confluence_score,
        confluence_direction=confluence_dir
    )
