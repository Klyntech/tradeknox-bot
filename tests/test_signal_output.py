"""Tests for signal output formatting."""

import pytest


class TestFormatSignalMessage:
    """Test the format_signal_message function."""

    def test_basic_message_structure(self):
        """Message should contain all required fields."""
        from signal_output import format_signal_message

        msg = format_signal_message(
            symbol="XAUUSD",
            direction="buy",
            entry=2400.0,
            stop_loss=2390.0,
            tp1=2415.0,
            tp2=2425.0,
            tp3=2435.0,
            rr1=1.5,
            rr2=2.5,
            rr3=3.5,
            confidence=72.0,
            score=15,
            max_score=20,
            session="london",
            reason="OB + FVG confluence",
        )

        assert "BUY" in msg
        assert "XAUUSD" in msg
        assert "Entry" in msg
        assert "Stop Loss" in msg
        assert "TP1" in msg
        assert "TP2" in msg
        assert "TP3" in msg
        assert "72.0%" in msg
        assert "15/20" in msg

    def test_sell_direction(self):
        """Sell signals should show SELL."""
        from signal_output import format_signal_message

        msg = format_signal_message(
            symbol="GBPJPY",
            direction="sell",
            entry=192.500,
            stop_loss=193.000,
            tp1=191.500,
            tp2=191.000,
            tp3=190.500,
            rr1=2.0,
            rr2=3.0,
            rr3=4.0,
            confidence=68.0,
            score=13,
            max_score=20,
            session="overlap",
            reason="Bearish BOS",
        )

        assert "SELL" in msg
        assert "GBPJPY" in msg

    def test_gold_price_formatting(self):
        """XAUUSD prices should have 2 decimal places."""
        from signal_output import format_signal_message

        msg = format_signal_message(
            symbol="XAUUSD",
            direction="buy",
            entry=2400.50,
            stop_loss=2390.25,
            tp1=2415.75,
            tp2=2425.00,
            tp3=2435.50,
            rr1=1.5,
            rr2=2.5,
            rr3=3.5,
            confidence=72.0,
            score=15,
            max_score=20,
            session="london",
            reason="Test",
        )

        assert "2400.50" in msg
        assert "2390.25" in msg


class TestFormatPrice:
    """Test price formatting per instrument."""

    def test_xauusd_two_decimals(self):
        from signal_output import format_price
        assert format_price(2400.5, "XAUUSD") == "2400.50"

    def test_gbpjpy_three_decimals(self):
        from signal_output import format_price
        assert format_price(192.5, "GBPJPY") == "192.500"

    def test_other_five_decimals(self):
        from signal_output import format_price
        assert format_price(1.23456, "EURUSD") == "1.23456"
