"""Tests for scoring engine — verify signal scoring logic."""

import pytest
from unittest.mock import MagicMock


class TestScoreSignal:
    """Test the score_signal function with various inputs."""

    def test_min_score_threshold(self):
        """Signals below threshold should not pass."""
        from scoring_engine import SignalScore

        score = SignalScore(
            total=10, max_possible=20, confidence_pct=60.0,
            breakdown={}, passed=False, reject_reason="below threshold"
        )
        assert not score.passed
        assert score.total < 11

    def test_signal_passes_at_threshold(self):
        """Signals at exactly 11/20 should pass."""
        from scoring_engine import SignalScore

        score = SignalScore(
            total=11, max_possible=20, confidence_pct=60.0,
            breakdown={}, passed=True, reject_reason=None
        )
        assert score.passed
        assert score.total >= 11

    def test_confidence_below_minimum(self):
        """Signals with confidence below 55% should not pass."""
        from scoring_engine import SignalScore

        score = SignalScore(
            total=15, max_possible=20, confidence_pct=50.0,
            breakdown={}, passed=False, reject_reason="low confidence"
        )
        assert not score.passed
        assert score.confidence_pct < 55.0

    def test_max_score_possible(self):
        """Maximum possible score is 20."""
        from scoring_engine import SignalScore

        score = SignalScore(
            total=20, max_possible=20, confidence_pct=100.0,
            breakdown={}, passed=True, reject_reason=None
        )
        assert score.total == score.max_possible == 20


class TestBuildRiskProfile:
    """Test risk profile calculation."""

    def test_valid_risk_profile(self):
        """Valid entry/SL/TP should produce valid risk profile."""
        from scoring_engine import build_risk_profile
        from config import BotConfig

        config = BotConfig()
        risk = build_risk_profile(
            entry=2400.0, stop_loss=2390.0,
            tp1=2415.0, tp2=2425.0, tp3=2435.0,
            account_balance=10000.0, config=config
        )
        assert risk.valid
        assert risk.rr_tp1 > 0
        assert risk.position_size > 0

    def test_invalid_rr_rejected(self):
        """Risk:Reward below 1.5 should be rejected."""
        from scoring_engine import build_risk_profile
        from config import BotConfig

        config = BotConfig()
        # Entry at 2400, SL at 2390 (10 risk), TP at 2405 (5 reward) = 0.5 RR
        risk = build_risk_profile(
            entry=2400.0, stop_loss=2390.0,
            tp1=2405.0, tp2=2410.0, tp3=2415.0,
            account_balance=10000.0, config=config
        )
        assert not risk.valid


class TestIsNewsBlackout:
    """Test news blackout detection."""

    def test_no_news_key_returns_false(self):
        """Without NEWS_API_KEY, should never be in blackout."""
        from scoring_engine import is_news_blackout
        from config import BotConfig

        config = BotConfig()
        config.NEWS_API_KEY = ""
        in_blackout, reason = is_news_blackout("XAUUSD", config)
        assert not in_blackout
