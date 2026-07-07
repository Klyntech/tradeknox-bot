"""Tests for subscription and license key system."""

import os
import pytest
from datetime import datetime, timezone, timedelta


class TestLicenseKeyGeneration:
    """Test license key generation and validation."""

    def test_key_format(self):
        """License key should start with TK-."""
        from subscriptions import generate_license_key

        key = generate_license_key("12345", "pro", 30)
        assert key.startswith("TK-")

    def test_key_contains_payload(self):
        """Key should contain base64-encoded payload."""
        from subscriptions import generate_license_key

        key = generate_license_key("12345", "pro", 30)
        parts = key.split("-")
        assert len(parts) >= 3  # TK-payload-signature

    def test_different_tiers_produce_different_keys(self):
        """Pro and VIP keys should be different."""
        from subscriptions import generate_license_key

        pro_key = generate_license_key("12345", "pro", 30)
        vip_key = generate_license_key("12345", "vip", 30)
        assert pro_key != vip_key


class TestLicenseKeyValidation:
    """Test license key validation."""

    def test_valid_key_passes(self):
        """A freshly generated key should validate."""
        from subscriptions import generate_license_key, validate_license_key

        key = generate_license_key("12345", "pro", 30)
        valid, payload, msg = validate_license_key(key)
        assert valid
        assert payload["tier"] == "pro"
        assert payload["uid"] == "12345"

    def test_tampered_key_fails(self):
        """A tampered key should fail validation."""
        from subscriptions import generate_license_key, validate_license_key

        key = generate_license_key("12345", "pro", 30)
        tampered = key[:-5] + "XXXXX"
        valid, _, _ = validate_license_key(tampered)
        assert not valid

    @pytest.mark.skipif(
        not os.environ.get("LICENSE_SECRET"),
        reason="LICENSE_SECRET not set — expired check uses auto-generated secret"
    )
    def test_expired_key_fails(self):
        """Key with 0 duration should be expired."""
        from subscriptions import generate_license_key, validate_license_key

        key = generate_license_key("12345", "pro", 0)
        valid, _, msg = validate_license_key(key)
        assert not valid
        assert "expired" in msg.lower()


class TestTierDurations:
    """Test tier duration constants."""

    def test_pro_duration(self):
        from subscriptions import TIER_DURATIONS
        assert TIER_DURATIONS["pro"] == 30

    def test_vip_duration(self):
        from subscriptions import TIER_DURATIONS
        assert TIER_DURATIONS["vip"] == 30
