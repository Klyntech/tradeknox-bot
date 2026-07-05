"""
Layer 4–6: Indicator Confluence, Risk Management & Scoring Engine
The gate keeper. Below threshold = NO TRADE. Not 'maybe trade'.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Layer 4: Indicator Confluence
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class IndicatorSignal:
    rsi_signal: str          # "bullish" | "bearish" | "neutral"
    rsi_divergence: bool
    ema_bias: str            # "bullish" | "bearish" | "mixed"
    above_trend_ema: bool    # price above 200 EMA
    volume_elevated: bool    # RVOL > 1.2
    atr_value: float
    details: Dict[str, float]


def assess_indicators(df: pd.DataFrame, direction: str, config) -> IndicatorSignal:
    """Assess indicator confluence for the given direction."""
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last

    rsi = last.get("rsi", 50)
    ema_fast = last.get("ema_fast", last["close"])
    ema_slow = last.get("ema_slow", last["close"])
    ema_trend = last.get("ema_trend", last["close"])
    rvol = last.get("rvol", 1.0)
    atr = last.get("atr", 1.0)

    # RSI signal
    if direction == "buy":
        rsi_signal = "bullish" if 40 <= rsi <= 65 else ("neutral" if rsi < 70 else "bearish")
    else:
        rsi_signal = "bearish" if 35 <= rsi <= 60 else ("neutral" if rsi > 30 else "bullish")

    # RSI divergence (simplified: price makes new extreme but RSI doesn't)
    rsi_div = False
    if len(df) >= 10:
        recent_close = df["close"].tail(10)
        recent_rsi = df["rsi"].tail(10)
        if direction == "buy":
            # Bullish div: price lower low, RSI higher low
            rsi_div = (recent_close.iloc[-1] < recent_close.min() and
                       recent_rsi.iloc[-1] > recent_rsi.min())
        else:
            # Bearish div: price higher high, RSI lower high
            rsi_div = (recent_close.iloc[-1] > recent_close.max() and
                       recent_rsi.iloc[-1] < recent_rsi.max())

    # EMA bias
    if ema_fast > ema_slow and last["close"] > ema_trend:
        ema_bias = "bullish"
    elif ema_fast < ema_slow and last["close"] < ema_trend:
        ema_bias = "bearish"
    else:
        ema_bias = "mixed"

    above_trend = last["close"] > ema_trend
    volume_elevated = rvol >= 1.2 if not pd.isna(rvol) else False

    return IndicatorSignal(
        rsi_signal=rsi_signal,
        rsi_divergence=rsi_div,
        ema_bias=ema_bias,
        above_trend_ema=above_trend,
        volume_elevated=volume_elevated,
        atr_value=float(atr),
        details={
            "rsi": round(float(rsi), 2),
            "ema_fast": round(float(ema_fast), 5),
            "ema_slow": round(float(ema_slow), 5),
            "ema_trend": round(float(ema_trend), 5),
            "rvol": round(float(rvol) if not pd.isna(rvol) else 1.0, 2),
        }
    )


# ──────────────────────────────────────────────────────────────────────────────
# Layer 5: Risk Management
# ──────────────────────────────────────────────────────────────────────────────

def calculate_position_size(account_balance: float, risk_pct: float,
                             entry: float, stop_loss: float,
                             pip_value: float = 0.1) -> float:
    """
    Position size in lots.
    Formula: Lots = (Balance × Risk%) / (|Entry - SL| × pip_value_per_lot)
    Default pip_value = $0.1/pip for a mini lot (adjust per instrument).
    """
    risk_amount = account_balance * (risk_pct / 100)
    sl_distance = abs(entry - stop_loss)
    if sl_distance == 0:
        return 0.0

    # Convert price distance to pips (approximate)
    if entry > 100:  # Gold / indices — price in dollars
        pips = sl_distance
        pip_value_per_lot = 100  # $1 per pip per lot for XAUUSD
    else:  # Forex
        pips = sl_distance * 10000  # 4-decimal forex
        pip_value_per_lot = 10     # $10 per pip per standard lot

    lots = risk_amount / (pips * pip_value_per_lot)
    return round(max(0.01, min(lots, 100.0)), 2)


@dataclass
class RiskProfile:
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    rr_tp1: float
    rr_tp2: float
    rr_tp3: float
    position_size: float
    risk_amount: float
    valid: bool


def build_risk_profile(entry: float, stop_loss: float,
                       tp1: float, tp2: float, tp3: float,
                       account_balance: float, config) -> RiskProfile:
    risk = abs(entry - stop_loss)
    if risk == 0:
        return RiskProfile(stop_loss, tp1, tp2, tp3, 0, 0, 0, 0, 0, valid=False)

    rr1 = round(abs(tp1 - entry) / risk, 2)
    rr2 = round(abs(tp2 - entry) / risk, 2)
    rr3 = round(abs(tp3 - entry) / risk, 2)

    if rr1 < config.MIN_RR_RATIO:
        return RiskProfile(stop_loss, tp1, tp2, tp3, rr1, rr2, rr3, 0, 0, valid=False)

    lot_size = calculate_position_size(
        account_balance, config.DEFAULT_RISK_PCT, entry, stop_loss
    )
    risk_amount = account_balance * config.DEFAULT_RISK_PCT / 100

    return RiskProfile(
        stop_loss=stop_loss,
        tp1=tp1, tp2=tp2, tp3=tp3,
        rr_tp1=rr1, rr_tp2=rr2, rr_tp3=rr3,
        position_size=lot_size,
        risk_amount=round(risk_amount, 2),
        valid=True
    )


# ──────────────────────────────────────────────────────────────────────────────
# Layer 9: News Filter
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class NewsEvent:
    title: str
    impact: str          # "high" | "medium" | "low"
    currency: str
    time_utc: datetime


def fetch_upcoming_news(config) -> List[NewsEvent]:
    """
    Fetch upcoming economic events.
    Uses forexfactory-style API or falls back to a hardcoded schedule.
    In production: integrate with investing.com or forexfactory scraper.
    """
    try:
        # Attempt to fetch from a news API (requires NEWS_API_KEY)
        if config.NEWS_API_KEY:
            return _fetch_from_api(config.NEWS_API_KEY)
    except Exception as e:
        logger.warning(f"News API fetch failed: {e}. Using fallback.")

    # Fallback: return empty list (no filter applied — be cautious)
    return []


def _fetch_from_api(api_key: str) -> List[NewsEvent]:
    """Placeholder for real news API integration."""
    # In production, integrate with:
    # - https://nfs.faireconomy.media/ff_calendar_thisweek.json (ForexFactory)
    # - investing.com economic calendar API
    # - fxstreet.com event API
    return []


def is_news_blackout(symbol: str, config) -> Tuple[bool, str]:
    """
    Returns (True, reason) if we're in a news blackout window.
    Returns (False, "") if clear to trade.
    """
    now = datetime.now(timezone.utc)
    events = fetch_upcoming_news(config)

    # Currency pair mapping to affected currencies
    currency_map = {
        "XAUUSD": ["USD", "XAU"],
        "EURUSD": ["EUR", "USD"],
        "GBPUSD": ["GBP", "USD"],
        "USDJPY": ["USD", "JPY"],
        "GBPJPY": ["GBP", "JPY"],
    }

    affected_currencies = currency_map.get(symbol, ["USD"])

    for event in events:
        if event.impact != "high":
            continue
        if event.currency not in affected_currencies:
            continue

        time_to_event = (event.time_utc - now).total_seconds() / 60
        time_since_event = (now - event.time_utc).total_seconds() / 60

        if 0 < time_to_event <= config.NEWS_BLACKOUT_BEFORE_MIN:
            return True, f"High-impact news in {int(time_to_event)}m: {event.title}"

        if 0 < time_since_event <= config.NEWS_BLACKOUT_AFTER_MIN:
            return True, f"Post-news blackout ({int(time_since_event)}m ago): {event.title}"

    return False, ""


# ──────────────────────────────────────────────────────────────────────────────
# Layer 6: Scoring Engine
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SignalScore:
    total: int
    max_possible: int
    confidence_pct: float
    breakdown: Dict[str, int]
    passed: bool
    reject_reason: str


def score_signal(structure,
                 entry_setup,
                 indicator_signal: IndicatorSignal,
                 session: str,
                 news_clear: bool,
                 config,
                 strategy_confluence=None) -> SignalScore:
    """
    Assign scores per category, compute confidence, apply threshold gate.
    Below MIN_SCORE_THRESHOLD = NO TRADE.
    """
    weights = config.SCORE_WEIGHTS
    breakdown = {}
    direction = entry_setup.direction

    # ── 1. Market Structure Score (max 5) ──────────────────────────────────
    ms_score = 0

    # Trend alignment
    from market_structure import Trend
    if direction == "buy" and structure.trend == Trend.BULLISH:
        ms_score += 2
    elif direction == "sell" and structure.trend == Trend.BEARISH:
        ms_score += 2
    # Flat (ranging) = 0 trend points

    # BOS/CHoCH confirmation
    if structure.last_bos and structure.last_bos.direction == ("bullish" if direction == "buy" else "bearish"):
        ms_score += 2
    if structure.last_choch and structure.last_choch.direction == ("bullish" if direction == "buy" else "bearish"):
        ms_score += 1  # CHoCH is a bonus — potential reversal

    # Price in discount (buy) or premium (sell)
    if direction == "buy" and structure.current_price_zone == "discount":
        ms_score += 1
    elif direction == "sell" and structure.current_price_zone == "premium":
        ms_score += 1

    ms_score = min(ms_score, weights["market_structure"])
    breakdown["market_structure"] = ms_score

    # ── 2. Entry Zone Score (max 4) ────────────────────────────────────────
    ez_score = 0

    if entry_setup.order_block:
        ez_score += 2 if entry_setup.order_block.strength >= 2 else 1
    if entry_setup.fvg:
        ez_score += 1
    if entry_setup.fib_confluence:
        ez_score += 1
    if entry_setup.candle_confirmed:
        ez_score += 1

    ez_score = min(ez_score, weights["entry_zone"])
    breakdown["entry_zone"] = ez_score

    # ── 3. Indicators Score (max 3) ────────────────────────────────────────
    ind_score = 0

    expected_rsi = "bullish" if direction == "buy" else "bearish"
    if indicator_signal.rsi_signal == expected_rsi:
        ind_score += 1
    if indicator_signal.rsi_divergence:
        ind_score += 1

    expected_ema = "bullish" if direction == "buy" else "bearish"
    if indicator_signal.ema_bias == expected_ema:
        ind_score += 1

    if indicator_signal.volume_elevated:
        ind_score += 1

    ind_score = min(ind_score, weights["indicators"])
    breakdown["indicators"] = ind_score

    # ── 4. Strategy Confluence Score (max 3) ───────────────────────────────
    strat_score = 0
    if strategy_confluence:
        # Each strategy agreeing with direction = 1 point (max 3)
        strat_direction = "bullish" if direction == "buy" else "bearish"
        if strategy_confluence.ma_direction == strat_direction:
            strat_score += 1
        if strategy_confluence.breakout_direction == strat_direction:
            strat_score += 1
        if strategy_confluence.ema_direction == strat_direction:
            strat_score += 1

    strat_score = min(strat_score, weights.get("strategy_confluence", 3))
    breakdown["strategy_confluence"] = strat_score

    # ── 5. Session Timing Score (max 3) ────────────────────────────────────
    session_scores = {
        "overlap":   3,
        "london":    2,
        "new_york":  2,
        "asia":      1,
        "dead_zone": 0,
    }
    sess_score = min(session_scores.get(session, 0), weights["session_timing"])
    breakdown["session_timing"] = sess_score

    # ── 6. News Clear Score (max 2) ────────────────────────────────────────
    news_score = weights["news_clear"] if news_clear else 0
    breakdown["news_clear"] = news_score

    # ── Final Score ────────────────────────────────────────────────────────
    total = sum(breakdown.values())
    max_possible = sum(weights.values())
    confidence = round((total / max_possible) * 100, 1)

    passed = (total >= config.MIN_SCORE_THRESHOLD and
              confidence >= config.MIN_CONFIDENCE_PCT)

    reject_reason = ""
    if not passed:
        if total < config.MIN_SCORE_THRESHOLD:
            reject_reason = f"Score {total}/{max_possible} below threshold ({config.MIN_SCORE_THRESHOLD})"
        elif confidence < config.MIN_CONFIDENCE_PCT:
            reject_reason = f"Confidence {confidence}% below minimum ({config.MIN_CONFIDENCE_PCT}%)"

    return SignalScore(
        total=total,
        max_possible=max_possible,
        confidence_pct=confidence,
        breakdown=breakdown,
        passed=passed,
        reject_reason=reject_reason
    )
