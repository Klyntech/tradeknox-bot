"""
Trading Strategies — Research-Backed (Multi-Timeframe + New Strategies)

Best strategies per pair from 3.5-year backtest (yfinance daily data):

XAUUSD (Best pair):
  - EMA Crossover (MM-008): WR 58.0%, PF 2.17, Return +66.08%
  - MA Crossover 9/21: WR 56.1%, PF 2.01, Return +66.83%
  - Heikin Ashi Trend (MM-017): WR 55.9%, PF 1.67, Return +47.61%
  - Stochastic Extreme (MM-016): WR 58.5%, PF 1.76, Return +18.62%

GBPJPY:
  - Stochastic Extreme (MM-016): WR 54.2%, PF 1.69, Return +7.08%
  - Heikin Ashi Trend (MM-017): WR 45.6%, PF 1.40, Return +13.66%
  - EMA Crossover (MM-008): WR 45.9%, PF 1.39, Return +12.44%

USDJPY (Now profitable with new strategies):
  - EMA Crossover (MM-008): WR 52.1%, PF 1.82, Return +22.18%
  - MA Crossover 9/21: WR 51.9%, PF 1.78, Return +24.16%
  - Heikin Ashi Trend (MM-017): WR 47.1%, PF 1.61, Return +20.78%

EURUSD (Excluded — consistently unprofitable):
  - MA Crossover: WR 40.3%, PF 1.28 (best, but weak)

GBPUSD (Excluded — mixed results):
  - MA Crossover: WR 46.1%, PF 1.43 (best, but inconsistent)

AUDUSD (New — 4h data):
  - MA Crossover 50/200: PF 1.93, WR 56.2%, 16 trades (small sample)
  - MA Crossover 9/21: PF 1.00, WR 40.0%

NZDUSD (New — 4h data):
  - MA Crossover 9/21: PF 1.52, WR 50.4%, Sharpe 0.208
  - MA Crossover 21/50: PF 1.67, WR 52.7%, Sharpe 0.255

USDCAD (New — 4h data):
  - Breakout all lookbacks: PF > 1.25 (highest of any pair)
  - MA Crossover 9/21: PF 1.41, WR 48.5%
  - MA Crossover 50/200: PF 3.75, WR 71.4% (14 trades)
"""

import logging
from dataclasses import dataclass
from typing import Dict

import pandas as pd

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
# Strategy 6: EMA Crossover (MM-008) — Trend Following
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class EMACrossoverSignal:
    direction: str
    fast_ema: float
    slow_ema: float
    trend_ema: float
    cross_type: str
    strength: float
    bars_since_cross: int


def detect_ema_crossover(df: pd.DataFrame, fast_period: int = 9,
                         slow_period: int = 21, trend_period: int = 100) -> EMACrossoverSignal:
    """
    EMA Crossover Strategy (MM-008):
    BUY: Fast EMA crosses above Slow EMA AND close > Trend EMA (100).
    SELL: Fast EMA crosses below Slow EMA AND close < Trend EMA (100).
    
    Trend-following strategy for trending markets.
    """
    if len(df) < trend_period + 10:
        return EMACrossoverSignal("neutral", 0, 0, 0, "none", 0.0, 0)

    # Calculate EMAs
    fast_ema = df["close"].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df["close"].ewm(span=slow_period, adjust=False).mean()
    trend_ema = df["close"].ewm(span=trend_period, adjust=False).mean()

    current_fast = fast_ema.iloc[-1]
    current_slow = slow_ema.iloc[-1]
    current_trend = trend_ema.iloc[-1]
    current_price = df["close"].iloc[-1]
    prev_fast = fast_ema.iloc[-2]
    prev_slow = slow_ema.iloc[-2]

    cross_type = "none"
    direction = "neutral"
    bars_since = 0

    # Golden Cross: fast crosses above slow
    if prev_fast <= prev_slow and current_fast > current_slow:
        cross_type = "golden"
        # Confirm with trend: close must be above trend EMA
        if current_price > current_trend:
            direction = "bullish"
        else:
            cross_type = "none"  # No confirmation

    # Death Cross: fast crosses below slow
    elif prev_fast >= prev_slow and current_fast < current_slow:
        cross_type = "death"
        # Confirm with trend: close must be below trend EMA
        if current_price < current_trend:
            direction = "bearish"
        else:
            cross_type = "none"  # No confirmation

    # Count bars since last cross
    if cross_type != "none":
        bars_since = 0
    else:
        for i in range(2, min(50, len(df))):
            prev_f = fast_ema.iloc[-(i+1)]
            prev_s = slow_ema.iloc[-(i+1)]
            curr_f = fast_ema.iloc[-i]
            curr_s = slow_ema.iloc[-i]
            if (prev_f <= prev_s and curr_f > curr_s) or \
               (prev_f >= prev_s and curr_f < curr_s):
                bars_since = i - 1
                if current_fast > current_slow:
                    direction = "bullish"
                else:
                    direction = "bearish"
                break

    # Calculate strength based on separation and trend alignment
    atr = df["atr"].iloc[-1] if "atr" in df.columns else 1.0
    separation = abs(current_fast - current_slow)
    strength = min(1.0, separation / (atr * 3)) if atr > 0 else 0.0

    return EMACrossoverSignal(
        direction=direction,
        fast_ema=round(current_fast, 5),
        slow_ema=round(current_slow, 5),
        trend_ema=round(current_trend, 5),
        cross_type=cross_type,
        strength=round(strength, 3),
        bars_since_cross=bars_since
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 7: Heikin Ashi Trend (MM-017) — Smooth Trend Following
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class HeikinAshiSignal:
    direction: str
    consecutive_bullish: int
    consecutive_bearish: int
    strength: float
    trend_aligned: bool


def detect_heikin_ashi_trend(df: pd.DataFrame, min_consecutive: int = 3) -> HeikinAshiSignal:
    """
    Heikin Ashi Trend Strategy (MM-017):
    BUY: 3+ consecutive bullish Heikin Ashi candles.
    SELL: 3+ consecutive bearish Heikin Ashi candles.
    
    Smooth trending moves with reduced noise.
    """
    if len(df) < 10:
        return HeikinAshiSignal("neutral", 0, 0, 0.0, False)

    # Calculate Heikin Ashi candles
    ha_close = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    
    # HA open: average of previous HA open and close
    ha_open = pd.Series(index=df.index, dtype=float)
    ha_open.iloc[0] = (df["open"].iloc[0] + df["close"].iloc[0]) / 2
    for i in range(1, len(df)):
        ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2

    # Count consecutive bullish/bearish candles
    bullish_count = 0
    bearish_count = 0

    # Check current candle direction
    for i in range(len(df)-1, max(0, len(df)-20), -1):
        is_bullish = ha_close.iloc[i] > ha_open.iloc[i]
        is_bearish = ha_close.iloc[i] < ha_open.iloc[i]

        if is_bullish:
            if bearish_count > 0:
                break
            bullish_count += 1
        elif is_bearish:
            if bullish_count > 0:
                break
            bearish_count += 1
        else:
            break

    # Determine direction
    direction = "neutral"
    strength = 0.0
    trend_aligned = False

    if bullish_count >= min_consecutive:
        direction = "bullish"
        strength = min(1.0, bullish_count / 5)
        # Check if aligned with overall trend (price above EMA 50)
        ema_50 = df["close"].ewm(span=50, adjust=False).mean().iloc[-1]
        trend_aligned = df["close"].iloc[-1] > ema_50
    elif bearish_count >= min_consecutive:
        direction = "bearish"
        strength = min(1.0, bearish_count / 5)
        # Check if aligned with overall trend
        ema_50 = df["close"].ewm(span=50, adjust=False).mean().iloc[-1]
        trend_aligned = df["close"].iloc[-1] < ema_50

    return HeikinAshiSignal(
        direction=direction,
        consecutive_bullish=bullish_count,
        consecutive_bearish=bearish_count,
        strength=round(strength, 3),
        trend_aligned=trend_aligned
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 8: Stochastic Extreme Reversal (MM-016)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class StochasticExtremeSignal:
    direction: str
    k_value: float
    d_value: float
    level: str
    cross_type: str
    strength: float


def detect_stochastic_extreme(df: pd.DataFrame, k_period: int = 14,
                              d_period: int = 3, oversold: float = 20,
                              overbought: float = 80) -> StochasticExtremeSignal:
    """
    Stochastic Extreme Reversal (MM-016):
    BUY: K crosses above D while K is near oversold (< 35).
    SELL: K crosses below D while K is near overbought (> 65).
    
    Reversal strategy at exhaustion points.
    """
    if len(df) < k_period + d_period + 5:
        return StochasticExtremeSignal("neutral", 50, 50, "neutral", "none", 0.0)

    # Calculate Stochastic
    low_min = df["low"].rolling(window=k_period).min()
    high_max = df["high"].rolling(window=k_period).max()

    denominator = high_max - low_min
    denominator = denominator.replace(0, 1)  # Avoid division by zero

    k = 100 * (df["close"] - low_min) / denominator
    d = k.rolling(window=d_period).mean()

    current_k = k.iloc[-1]
    current_d = d.iloc[-1]
    prev_k = k.iloc[-2]
    prev_d = d.iloc[-2]

    # Determine level
    level = "neutral"
    if current_k < oversold + 15:  # Near oversold (35)
        level = "oversold"
    elif current_k > overbought - 15:  # Near overbought (65)
        level = "overbought"

    # Detect crossover
    cross_type = "none"
    direction = "neutral"
    strength = 0.0

    # Bullish cross: K crosses above D near oversold
    if prev_k <= prev_d and current_k > current_d and level == "oversold":
        cross_type = "golden"
        direction = "bullish"
        strength = min(1.0, (oversold + 15 - current_k) / (oversold + 15))

    # Bearish cross: K crosses below D near overbought
    elif prev_k >= prev_d and current_k < current_d and level == "overbought":
        cross_type = "death"
        direction = "bearish"
        strength = min(1.0, (current_k - (overbought - 15)) / (100 - (overbought - 15)))

    return StochasticExtremeSignal(
        direction=direction,
        k_value=round(current_k, 1),
        d_value=round(current_d, 1),
        level=level,
        cross_type=cross_type,
        strength=round(strength, 3)
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
    ema_crossover_direction: str
    ema_crossover_strength: float
    heikin_ashi_direction: str
    heikin_ashi_strength: float
    stochastic_direction: str
    stochastic_strength: float
    confluence_score: int     # 0-3
    confluence_direction: str
    day_filter: str           # "best" | "avoid" | "neutral"
    day_name: str


# Per-pair optimal strategy configs (from research)
PAIR_STRATEGIES: Dict[str, Dict] = {
    "XAUUSD": {
        "timeframe": "4h",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 10,
        "rsi_oversold": 30, "rsi_overbought": 70,
        "ema_fast": 9, "ema_slow": 21, "ema_trend": 100,
        "weights": {"breakout": 2, "ma": 1, "ema_crossover": 2, "heikin_ashi": 1, "stochastic": 0},
        "best_days": ["Thursday", "Friday"],  # Breakout PF 1.74-1.94, MA PF 2.14
        "avoid_days": ["Monday"],              # MA 9/21 PF 0.81
    },
    "EURUSD": {
        "timeframe": "15m",
        "ma_fast": 21, "ma_slow": 50,
        "breakout_lookback": 20,
        "rsi_oversold": 25, "rsi_overbought": 75,
        "ema_fast": 9, "ema_slow": 21, "ema_trend": 100,
        "weights": {"ma": 2, "ema_crossover": 1, "heikin_ashi": 0, "breakout": 0, "stochastic": 0},
        "best_days": ["Tuesday", "Monday"],    # MA 21/50 PF 2.4, MA 9/21 PF 1.59
        "avoid_days": ["Friday"],              # MA 9/21 PF 0.4, RSI PF 0.51
    },
    "GBPUSD": {
        "timeframe": "4h",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 20,
        "rsi_oversold": 30, "rsi_overbought": 70,
        "ema_fast": 9, "ema_slow": 21, "ema_trend": 100,
        "weights": {"ma": 2, "ema_crossover": 1, "heikin_ashi": 0, "breakout": 1, "stochastic": 0},
        "best_days": ["Friday", "Tuesday"],    # MA 9/21 PF 2.57, MA 9/21 PF 1.69
        "avoid_days": ["Thursday"],            # Breakout 50 PF 0.63
    },
    "USDJPY": {
        "timeframe": "4h",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 10,
        "rsi_oversold": 20, "rsi_overbought": 80,
        "ema_fast": 9, "ema_slow": 21, "ema_trend": 100,
        "weights": {"ema_crossover": 2, "ma": 1, "heikin_ashi": 1, "breakout": 1, "stochastic": 1},
        "best_days": ["Monday", "Wednesday"],  # EMA Crossover PF 1.82, MA PF 1.78
        "avoid_days": ["Friday"],              # Lower liquidity
    },
    "GBPJPY": {
        "timeframe": "4h",
        "ma_fast": 50, "ma_slow": 200,
        "breakout_lookback": 20,
        "rsi_oversold": 20, "rsi_overbought": 80,
        "ema_fast": 9, "ema_slow": 21, "ema_trend": 100,
        "weights": {"rsi": 2, "ma": 1, "heikin_ashi": 1, "stochastic": 1, "ema_crossover": 0, "breakout": 0},
        "best_days": ["Thursday", "Wednesday"],  # RSI 20/80 PF 4.71, RSI 25/75 PF 1.5
        "avoid_days": ["Wednesday"],             # EMA Align PF 0.66
    },
    "AUDUSD": {
        "timeframe": "4h",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 20,
        "rsi_oversold": 30, "rsi_overbought": 70,
        "ema_fast": 9, "ema_slow": 21, "ema_trend": 100,
        "weights": {"ma": 2, "ema_crossover": 1, "breakout": 0, "heikin_ashi": 0, "stochastic": 0},
        "best_days": ["Tuesday", "Thursday"],
        "avoid_days": ["Monday"],
    },
    "NZDUSD": {
        "timeframe": "4h",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 10,
        "rsi_oversold": 30, "rsi_overbought": 70,
        "ema_fast": 9, "ema_slow": 21, "ema_trend": 100,
        "weights": {"ma": 2, "ema_crossover": 1, "breakout": 0, "heikin_ashi": 0, "stochastic": 0},
        "best_days": ["Wednesday", "Friday"],
        "avoid_days": ["Monday"],
    },
    "USDCAD": {
        "timeframe": "4h",
        "ma_fast": 9, "ma_slow": 21,
        "breakout_lookback": 20,
        "rsi_oversold": 30, "rsi_overbought": 70,
        "ema_fast": 9, "ema_slow": 21, "ema_trend": 100,
        "weights": {"breakout": 2, "ma": 2, "ema_crossover": 1, "heikin_ashi": 0, "stochastic": 0},
        "best_days": ["Tuesday", "Thursday"],
        "avoid_days": ["Friday"],
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

    # Run EMA Crossover (MM-008)
    ema_crossover_signal = detect_ema_crossover(
        df, fast_period=pair_cfg.get("ema_fast", 9),
        slow_period=pair_cfg.get("ema_slow", 21),
        trend_period=pair_cfg.get("ema_trend", 100)
    )

    # Run Heikin Ashi Trend (MM-017)
    heikin_ashi_signal = detect_heikin_ashi_trend(df)

    # Run Stochastic Extreme (MM-016)
    stochastic_signal = detect_stochastic_extreme(df)

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

    if weights.get("ema_crossover", 0) > 0:
        max_score += weights["ema_crossover"]
        if ema_crossover_signal.direction == strat_direction:
            score += weights["ema_crossover"]

    if weights.get("heikin_ashi", 0) > 0:
        max_score += weights["heikin_ashi"]
        if heikin_ashi_signal.direction == strat_direction:
            score += weights["heikin_ashi"]

    if weights.get("stochastic", 0) > 0:
        max_score += weights["stochastic"]
        if stochastic_signal.direction == strat_direction:
            score += weights["stochastic"]

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

    if ema_crossover_signal.direction == "bullish":
        bullish_score += weights.get("ema_crossover", 0)
    elif ema_crossover_signal.direction == "bearish":
        bearish_score += weights.get("ema_crossover", 0)

    if heikin_ashi_signal.direction == "bullish":
        bullish_score += weights.get("heikin_ashi", 0)
    elif heikin_ashi_signal.direction == "bearish":
        bearish_score += weights.get("heikin_ashi", 0)

    if stochastic_signal.direction == "bullish":
        bullish_score += weights.get("stochastic", 0)
    elif stochastic_signal.direction == "bearish":
        bearish_score += weights.get("stochastic", 0)

    if bullish_score > bearish_score:
        confluence_dir = "bullish"
    elif bearish_score > bullish_score:
        confluence_dir = "bearish"
    else:
        confluence_dir = "neutral"

    # Day-of-week filter
    from datetime import datetime
    day_name = datetime.now().strftime("%A")
    best_days = pair_cfg.get("best_days", [])
    avoid_days = pair_cfg.get("avoid_days", [])

    if day_name in avoid_days:
        day_filter = "avoid"
        confluence_score = 0  # Zero out on bad days
    elif day_name in best_days:
        day_filter = "best"
        confluence_score = min(3, confluence_score + 1)  # Bonus on best days
    else:
        day_filter = "neutral"

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
        ema_crossover_direction=ema_crossover_signal.direction,
        ema_crossover_strength=ema_crossover_signal.strength,
        heikin_ashi_direction=heikin_ashi_signal.direction,
        heikin_ashi_strength=heikin_ashi_signal.strength,
        stochastic_direction=stochastic_signal.direction,
        stochastic_strength=stochastic_signal.strength,
        confluence_score=confluence_score,
        confluence_direction=confluence_dir,
        day_filter=day_filter,
        day_name=day_name
    )
