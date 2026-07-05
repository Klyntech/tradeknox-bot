"""
User Manager — Telegram user tracking, subscription gating, signal limits.

Handles:
- User registration on /start
- Tier checks before sending signals
- Daily signal count enforcement
- License key activation via /subscribe
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from subscriptions import (
    LicenseDatabase,
    generate_license_key,
    validate_license_key,
    get_tier_limits,
    TIER_DURATIONS,
)

logger = logging.getLogger(__name__)


class UserManager:
    """Manages Telegram users, their tiers, and signal access."""

    def __init__(self, db_path: str = "licenses.db"):
        self.db = LicenseDatabase(db_path)

    def register_user(self, user_id: str, username: str = None) -> dict:
        """Register a new user or return existing user data."""
        existing = self.db.get_user(user_id)
        if existing:
            if username and existing.get("username") != username:
                self.db.upsert_user(user_id, username, existing["tier"])
            return existing

        # New user — auto-assign free tier
        self.db.upsert_user(user_id, username, tier="free")
        logger.info(f"New user registered: {user_id} (@{username})")
        return self.db.get_user(user_id)

    def activate_license(self, user_id: str, license_key: str) -> Tuple[bool, str]:
        """
        Activate a license key for a user.
        Returns: (success, message)
        """
        valid, payload, error = validate_license_key(license_key)
        if not valid:
            return False, f"Invalid key: {error}"

        if payload["uid"] != user_id:
            return False, "Key belongs to another user"

        tier = payload["tier"]
        expires_at = payload["exp"]

        # Save license
        self.db.save_license(user_id, tier, license_key, expires_at)
        self.db.upsert_user(user_id, tier=tier, license_key=license_key)

        logger.info(f"License activated: {user_id} -> {tier} until {expires_at}")
        return True, f"Activated {tier.upper()} tier until {expires_at[:10]}"

    def get_user_tier(self, user_id: str) -> str:
        """Return the user's current tier (free/pro/vip)."""
        user = self.db.get_user(user_id)
        if not user:
            return "free"

        # Verify license is still valid
        license_info = self.db.get_active_license(user_id)
        if license_info:
            valid, payload, _ = validate_license_key(license_info["license_key"])
            if valid:
                return payload["tier"]
            else:
                # License expired — downgrade
                self.db.revoke_license(user_id)
                self.db.upsert_user(user_id, tier="free")
                return "free"

        return user.get("tier", "free")

    def can_receive_signal(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user can receive a signal right now.
        Returns: (can_receive, reason_if_not)
        """
        tier = self.get_user_tier(user_id)
        limits = get_tier_limits(tier)

        user = self.db.get_user(user_id)
        if not user:
            return True, ""  # New user, allow first signal

        signals_used = user.get("signals_used_today", 0)
        max_signals = limits["signals_per_day"]

        if signals_used >= max_signals:
            return False, f"Daily limit reached ({max_signals} signals/day for {tier.upper()})"

        return True, ""

    def record_signal_sent(self, user_id: str):
        """Increment the user's daily signal count."""
        self.db.increment_signals_used(user_id)

    def get_user_stats(self, user_id: str) -> dict:
        """Return user stats for /status command."""
        user = self.db.get_user(user_id)
        if not user:
            return {"registered": False}

        tier = self.get_user_tier(user_id)
        limits = get_tier_limits(tier)

        return {
            "registered": True,
            "user_id": user_id,
            "username": user.get("username"),
            "tier": tier,
            "signals_used_today": user.get("signals_used_today", 0),
            "signals_limit": limits["signals_per_day"],
            "delay_minutes": limits["delay_minutes"],
            "joined_at": user.get("joined_at"),
        }

    def generate_pro_key(self, user_id: str) -> str:
        """Generate a PRO license key for a user."""
        key = generate_license_key(user_id, "pro")
        expires = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        from datetime import timedelta
        expires += timedelta(days=TIER_DURATIONS["pro"])
        self.db.save_license(user_id, "pro", key, expires.isoformat())
        return key

    def generate_vip_key(self, user_id: str) -> str:
        """Generate a VIP license key for a user."""
        key = generate_license_key(user_id, "vip")
        expires = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        from datetime import timedelta
        expires += timedelta(days=TIER_DURATIONS["vip"])
        self.db.save_license(user_id, "vip", key, expires.isoformat())
        return key
