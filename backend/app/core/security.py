"""
AquaMediAI — Core Security & Cryptography Module
================================================
Provides NIST SP 800-132 compliant password hashing (PBKDF2-HMAC-SHA256),
RFC 7519 compatible JWT signing and verification (HS256), and in-memory
rate limiting for brute force prevention.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# PBKDF2 configuration
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 100_000
SALT_BYTES = 16


def hash_password(plain_password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a cryptographically secure random salt.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        plain_password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_hex = salt.hex()
    hash_hex = derived.hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_hex}${hash_hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a PBKDF2-HMAC-SHA256 hashed string using constant-time comparison.
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])

        computed = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(computed, expected_hash)
    except Exception as exc:
        logger.warning("Error verifying password: %s", exc)
        return False


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to base64url string without padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data_str: str) -> bytes:
    """Decode base64url string with padding restoration."""
    rem = len(data_str) % 4
    if rem > 0:
        data_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data_str.encode("utf-8"))


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create an RFC 7519 compliant JSON Web Token (JWT) signed with HMAC-SHA256.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=8)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    })

    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")

    header_b64 = _b64url_encode(header_json)
    payload_b64 = _b64url_encode(payload_json)
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT signature and expiration.
    Returns the payload dictionary if valid, or None if invalid/expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            logger.warning("Invalid token signature detected")
            return None

        # Parse payload
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp")
        if exp is not None:
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if now_ts > exp:
                logger.debug("Token expired: exp=%s, now=%s", exp, now_ts)
                return None

        return payload
    except Exception as exc:
        logger.warning("Token decode failure: %s", exc)
        return None


# ─── In-Memory Rate Limiter for Login Protection ──────────────────────────────

class LoginRateLimiter:
    """
    Thread-safe in-memory rate limiter to prevent brute-force attacks on login endpoints.
    Tracks failed attempts by client identifier (IP or username).
    """

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 900) -> None:
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        # Mapping: key -> (failed_count, lockout_until_timestamp)
        self._records: Dict[str, Tuple[int, float]] = {}

    def is_locked_out(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if identifier is currently locked out.
        Returns (is_locked, remaining_seconds).
        """
        now = time.time()
        record = self._records.get(identifier)
        if not record:
            return False, 0

        failed_count, lockout_until = record
        if now < lockout_until:
            remaining = int(lockout_until - now)
            return True, remaining

        # Lockout expired
        if lockout_until > 0 and now >= lockout_until:
            self._records.pop(identifier, None)
            return False, 0

        return False, 0

    def record_failure(self, identifier: str) -> Tuple[bool, int]:
        """
        Record a failed login attempt.
        Returns (is_locked_now, remaining_seconds_or_attempts_left).
        """
        now = time.time()
        record = self._records.get(identifier)
        if not record:
            self._records[identifier] = (1, 0.0)
            return False, self.max_attempts - 1

        failed_count, lockout_until = record
        if now < lockout_until:
            return True, int(lockout_until - now)

        new_count = failed_count + 1
        if new_count >= self.max_attempts:
            new_lockout = now + self.lockout_seconds
            self._records[identifier] = (new_count, new_lockout)
            logger.warning(
                "Security alert: Identifier %s locked out for %d seconds after %d failed attempts",
                identifier,
                self.lockout_seconds,
                new_count,
            )
            return True, self.lockout_seconds

        self._records[identifier] = (new_count, 0.0)
        return False, self.max_attempts - new_count

    def record_success(self, identifier: str) -> None:
        """Clear failed attempts on successful authentication."""
        self._records.pop(identifier, None)


# Default global rate limiter instance
login_rate_limiter = LoginRateLimiter(max_attempts=5, lockout_seconds=900)

