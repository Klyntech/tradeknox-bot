"""
Day-of-Week Filter — The only surviving "strategy" input.
All indicator-based strategies killed (MarketMate graveyard: MM-008, MM-016, MM-017, etc.).
TradeKnox runs on SMC 8-Gate pipeline alone.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Combined Strategy Assessment (Per-Pair, Multi-Timeframe)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class StrategyConfluence:
    day_filter: str           # "best" | "avoid" | "neutral"
    day_name: str
    confluence_score: int     # 0 — reserved for future use


# Per-pair day-of-week configs
PAIR_STRATEGIES: Dict[str, Dict] = {
    "XAUUSD": {
        "timeframe": "4h",
        "best_days": ["Thursday", "Friday"],
        "avoid_days": ["Monday"],
    },
    "EURUSD": {
        "timeframe": "15m",
        "best_days": ["Tuesday", "Monday"],
        "avoid_days": ["Friday"],
    },
    "GBPUSD": {
        "timeframe": "4h",
        "best_days": ["Friday", "Tuesday"],
        "avoid_days": ["Thursday"],
    },
    "USDJPY": {
        "timeframe": "4h",
        "best_days": ["Monday", "Wednesday"],
        "avoid_days": ["Friday"],
    },
    "GBPJPY": {
        "timeframe": "4h",
        "best_days": ["Thursday", "Wednesday"],
        "avoid_days": ["Wednesday"],
    },
    "AUDUSD": {
        "timeframe": "4h",
        "best_days": ["Tuesday", "Thursday"],
        "avoid_days": ["Monday"],
    },
    "NZDUSD": {
        "timeframe": "4h",
        "best_days": ["Wednesday", "Friday"],
        "avoid_days": ["Monday"],
    },
    "USDCAD": {
        "timeframe": "4h",
        "best_days": ["Tuesday", "Thursday"],
        "avoid_days": ["Friday"],
    },
}


def get_pair_config(symbol: str) -> Dict:
    """Get day-of-week config for a pair."""
    return PAIR_STRATEGIES.get(symbol, PAIR_STRATEGIES["XAUUSD"])


def assess_strategies(df, direction: str,
                      config, symbol: str = "XAUUSD") -> StrategyConfluence:
    """
    Day-of-week filter only. All indicator-based strategies removed.
    TradeKnox runs on SMC 8-Gate pipeline alone.
    """
    pair_cfg = get_pair_config(symbol)
    day_name = datetime.now().strftime("%A")
    best_days = pair_cfg.get("best_days", [])
    avoid_days = pair_cfg.get("avoid_days", [])

    if day_name in avoid_days:
        day_filter = "avoid"
    elif day_name in best_days:
        day_filter = "best"
    else:
        day_filter = "neutral"

    return StrategyConfluence(
        day_filter=day_filter,
        day_name=day_name,
        confluence_score=0,
    )
