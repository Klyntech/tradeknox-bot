"""
Subscription System — HMAC License Key Generation & Validation

License keys encode: user_id + tier + expiry timestamp
Signed with HMAC-SHA256 to prevent tampering.
"""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple


# Secret key for HMAC signing — set via env var or generate on first run
LICENSE_SECRET = os.getenv("LICENSE_SECRET", secrets.token_hex(32))

# Tier durations (days)
TIER_DURATIONS = {
    "free": 0,
    "pro": 30,
    "vip": 30,
}

# Tier limits
TIER_LIMITS = {
    "free": {"signals_per_day": 3, "delay_minutes": 15},
    "pro": {"signals_per_day": 999, "delay_minutes": 0},
    "vip": {"signals_per_day": 999, "delay_minutes": 0},
}


def _sign(data: str) -> str:
    """Generate HMAC-SHA256 signature."""
    return hmac.new(
        LICENSE_SECRET.encode(), data.encode(), hashlib.sha256
    ).hexdigest()[:16]


def generate_license_key(user_id: str, tier: str, duration_days: int = None) -> str:
    """
    Generate a signed license key.
    Format: base64(payload).signature
    Payload: {user_id, tier, expiry_iso}
    """
    if tier not in TIER_DURATIONS:
        raise ValueError(f"Invalid tier: {tier}")

    if duration_days is None:
        duration_days = TIER_DURATIONS[tier]

    if tier == "free":
        expiry = datetime.now(timezone.utc) + timedelta(days=365 * 10)  # effectively never
    else:
        expiry = datetime.now(timezone.utc) + timedelta(days=duration_days)

    payload = json.dumps({
        "uid": user_id,
        "tier": tier,
        "exp": expiry.isoformat(),
    }, separators=(",", ":"))

    encoded = urlsafe_b64encode(payload.encode()).decode()
    signature = _sign(encoded)

    return f"TK-{encoded}-{signature}"


def validate_license_key(key: str) -> Tuple[bool, Optional[dict], str]:
    """
    Validate a license key.
    Returns: (is_valid, payload_or_none, error_message)
    """
    if not key.startswith("TK-"):
        return False, None, "Invalid key format"

    parts = key.split("-")
    if len(parts) != 3:
        return False, None, "Invalid key structure"

    encoded = parts[1]
    signature = parts[2]

    # Verify signature
    expected_sig = _sign(encoded)
    if not hmac.compare_digest(signature, expected_sig):
        return False, None, "Invalid signature"

    # Decode payload
    try:
        payload = json.loads(urlsafe_b64decode(encoded))
    except Exception:
        return False, None, "Corrupted payload"

    # Check expiry
    expiry = datetime.fromisoformat(payload["exp"])
    if datetime.now(timezone.utc) > expiry:
        return False, None, "Key expired"

    return True, payload, ""


def get_tier_limits(tier: str) -> dict:
    """Return the limits for a given tier."""
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


# ──────────────────────────────────────────────────────────────────────────────
# License Key Database
# ──────────────────────────────────────────────────────────────────────────────

class LicenseDatabase:
    """SQLite store for license keys and user subscriptions."""

    def __init__(self, db_path: str = "licenses.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS licenses (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     TEXT NOT NULL,
                    tier        TEXT NOT NULL DEFAULT 'free',
                    license_key TEXT UNIQUE NOT NULL,
                    created_at  TEXT NOT NULL,
                    expires_at  TEXT NOT NULL,
                    active      INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     TEXT PRIMARY KEY,
                    username    TEXT,
                    tier        TEXT DEFAULT 'free',
                    license_key TEXT,
                    joined_at   TEXT,
                    last_scan   TEXT,
                    signals_used_today INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def save_license(self, user_id: str, tier: str, license_key: str,
                     expires_at: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO licenses (user_id, tier, license_key, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, tier, license_key,
                  datetime.now(timezone.utc).isoformat(), expires_at))
            conn.commit()

    def get_active_license(self, user_id: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM licenses
                WHERE user_id = ? AND active = 1
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,)).fetchone()
            return dict(row) if row else None

    def revoke_license(self, user_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE licenses SET active = 0 WHERE user_id = ?
            """, (user_id,))
            conn.commit()

    def upsert_user(self, user_id: str, username: str = None,
                    tier: str = "free", license_key: str = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO users (user_id, username, tier, license_key, joined_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = COALESCE(excluded.username, username),
                    tier = excluded.tier,
                    license_key = COALESCE(excluded.license_key, license_key)
            """, (user_id, username, tier, license_key,
                  datetime.now(timezone.utc).isoformat()))
            conn.commit()

    def get_user(self, user_id: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def increment_signals_used(self, user_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users SET signals_used_today = signals_used_today + 1,
                    last_scan = ?
                WHERE user_id = ?
            """, (datetime.now(timezone.utc).isoformat(), user_id))
            conn.commit()

    def reset_daily_signals(self):
        """Reset all daily signal counts. Call at midnight UTC."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE users SET signals_used_today = 0")
            conn.commit()
