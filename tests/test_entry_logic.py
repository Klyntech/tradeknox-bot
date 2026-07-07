"""Tests for entry logic — order block detection, FVG, etc."""

import pytest
import pandas as pd
import numpy as np


def _make_ohlcv(n=100, base_price=2400.0, volatility=5.0):
    """Generate synthetic OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2026-01-01", periods=n, freq="1h")
    close = base_price + np.cumsum(np.random.randn(n) * volatility)
    high = close + np.abs(np.random.randn(n) * volatility * 0.5)
    low = close - np.abs(np.random.randn(n) * volatility * 0.5)
    open_price = close + np.random.randn(n) * volatility * 0.3

    df = pd.DataFrame({
        "timestamp": dates,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(1000, 10000, n),
    })
    return df


class TestOrderBlockDetection:
    """Test order block detection logic."""

    def test_ob_returns_list(self):
        """detect_order_blocks should return a list."""
        from entry_logic import detect_order_blocks

        df = _make_ohlcv(50)
        obs = detect_order_blocks(df, lookback=20, atr=5.0)
        assert isinstance(obs, list)

    def test_ob_has_required_fields(self):
        """Each OB should have top, bottom, kind fields."""
        from entry_logic import detect_order_blocks

        df = _make_ohlcv(50)
        obs = detect_order_blocks(df, lookback=20, atr=5.0)
        for ob in obs:
            assert hasattr(ob, "top")
            assert hasattr(ob, "bottom")
            assert hasattr(ob, "kind")
            assert ob.kind in ("bullish", "bearish")


class TestFVGDetection:
    """Test Fair Value Gap detection."""

    def test_fvg_returns_list(self):
        """detect_fvg should return a list."""
        from entry_logic import detect_fvg

        df = _make_ohlcv(50)
        fvgs = detect_fvg(df, atr=5.0)
        assert isinstance(fvgs, list)

    def test_fvg_has_required_fields(self):
        """Each FVG should have top and bottom fields."""
        from entry_logic import detect_fvg

        df = _make_ohlcv(50)
        fvgs = detect_fvg(df, atr=5.0)
        for fvg in fvgs:
            assert hasattr(fvg, "top")
            assert hasattr(fvg, "bottom")
            assert fvg.top > fvg.bottom
