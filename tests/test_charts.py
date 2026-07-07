"""Tests for chart generation."""

import asyncio
import os
import pytest
import pandas as pd
import numpy as np


def _make_ohlcv(n=100, base_price=2400.0):
    """Generate synthetic OHLCV data."""
    np.random.seed(42)
    dates = pd.date_range("2026-01-01", periods=n, freq="1h")
    close = base_price + np.cumsum(np.random.randn(n) * 5)
    high = close + np.abs(np.random.randn(n) * 3)
    low = close - np.abs(np.random.randn(n) * 3)
    open_price = close + np.random.randn(n) * 2

    return pd.DataFrame({
        "timestamp": dates,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(1000, 10000, n),
    })


class TestRenderSignalChart:
    """Test the render_signal_chart function."""

    def test_renders_without_error(self):
        """Chart should render without raising exceptions."""
        from charts import render_signal_chart

        df = _make_ohlcv(50)
        signal = {
            "symbol": "XAUUSD",
            "direction": "BUY",
            "entry": 2450.0,
            "stop_loss": 2435.0,
            "tp1": 2470.0,
            "tp2": 2485.0,
            "tp3": 2500.0,
            "score": 15,
            "confidence": 72,
        }

        result = asyncio.run(render_signal_chart(signal=signal, df=df))
        assert result is not None
        assert os.path.exists(result)
        assert os.path.getsize(result) > 2048

        # Cleanup
        os.unlink(result)

    def test_returns_none_for_empty_df(self):
        """Empty DataFrame should return None."""
        from charts import render_signal_chart

        df = pd.DataFrame()
        signal = {"symbol": "XAUUSD", "direction": "BUY", "entry": 2400.0}

        result = asyncio.run(render_signal_chart(signal=signal, df=df))
        assert result is None

    def test_returns_none_for_insufficient_candles(self):
        """Less than 10 candles should return None."""
        from charts import render_signal_chart

        df = _make_ohlcv(5)
        signal = {"symbol": "XAUUSD", "direction": "BUY", "entry": 2400.0}

        result = asyncio.run(render_signal_chart(signal=signal, df=df))
        assert result is None

    def test_with_order_blocks(self):
        """Chart should render with OB annotations."""
        from charts import render_signal_chart

        df = _make_ohlcv(50)
        signal = {
            "symbol": "XAUUSD",
            "direction": "BUY",
            "entry": 2450.0,
            "stop_loss": 2435.0,
            "tp1": 2470.0,
            "tp2": 2485.0,
            "tp3": 2500.0,
            "score": 15,
            "confidence": 72,
        }
        order_blocks = [
            {"high": 2445.0, "low": 2440.0, "type": "demand"},
        ]

        result = asyncio.run(render_signal_chart(
            signal=signal, df=df, order_blocks=order_blocks
        ))
        assert result is not None
        os.unlink(result)

    def test_with_fvgs(self):
        """Chart should render with FVG annotations."""
        from charts import render_signal_chart

        df = _make_ohlcv(50)
        signal = {
            "symbol": "XAUUSD",
            "direction": "BUY",
            "entry": 2450.0,
            "stop_loss": 2435.0,
            "tp1": 2470.0,
            "tp2": 2485.0,
            "tp3": 2500.0,
            "score": 15,
            "confidence": 72,
        }
        fvgs = [{"high": 2460.0, "low": 2455.0}]

        result = asyncio.run(render_signal_chart(
            signal=signal, df=df, fvgs=fvgs
        ))
        assert result is not None
        os.unlink(result)


class TestRenderBlurredChart:
    """Test the blur effect for free tier."""

    def test_blur_produces_bytes(self):
        """Blur should produce valid PNG bytes."""
        from charts import render_signal_chart, render_blurred_chart

        df = _make_ohlcv(50)
        signal = {
            "symbol": "XAUUSD",
            "direction": "BUY",
            "entry": 2450.0,
            "stop_loss": 2435.0,
            "tp1": 2470.0,
            "tp2": 2485.0,
            "tp3": 2500.0,
            "score": 15,
            "confidence": 72,
        }

        chart_path = asyncio.run(render_signal_chart(signal=signal, df=df))
        assert chart_path is not None

        blurred = render_blurred_chart(chart_path)
        assert blurred is not None
        assert len(blurred) > 1000  # Should be a reasonable size

        os.unlink(chart_path)
