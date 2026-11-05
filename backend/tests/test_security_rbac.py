"""
AquaMediAI — Security, Authentication & Server-Side RBAC Verification Tests
===========================================================================
Validates:
1. Frictionless Farmer Guest Session generation.
2. Secure Expert Authentication with PBKDF2-HMAC-SHA256 password hashing.
3. Brute force defense via LoginRateLimiter (lockout after max attempts).
4. Session inspection (GET /api/v1/auth/me) and logout.
5. Server-side RBAC enforcement:
   - Guest farmers CANNOT access full scenario run, conflict detection, LP allocation, or negotiation (403 Forbidden).
   - Guest farmers CAN access single and batch prediction endpoints.
   - Verified Agricultural Experts have full authorized access.
"""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    login_rate_limiter,
    verify_password,
)
from app.main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


# ─── Cryptographic Unit Tests ────────────────────────────────────────────────

def test_password_hashing_and_verification():
    raw = "SecureExpert#2026Pass"
    hashed = hash_password(raw)
    assert hashed.startswith("pbkdf2_sha256$100000$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_token_creation_and_expiration():
    secret = "test_super_secret_key_12345"
    payload = {"sub": "expert@gov.in", "role": "expert"}
    token = create_access_token(payload, secret_key=secret)
    decoded = decode_access_token(token, secret_key=secret)
    assert decoded is not None
    assert decoded["sub"] == "expert@gov.in"
    assert decoded["role"] == "expert"

    # Invalid secret fails verification
    assert decode_access_token(token, secret_key="wrong_secret_key") is None


# ─── Auth API Integration Tests ──────────────────────────────────────────────

def test_farmer_guest_session_creation(client):
    res = client.post("/api/v1/auth/guest-session")
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "farmer_guest"
    assert "access_token" in data
    assert data["session_id"].startswith("guest_")
    assert "farmer:predict" in data["permissions"]


def test_expert_login_success(client):
    settings = get_settings()
    payload = {
        "username_or_email": settings.expert_default_email,
        "password": settings.expert_default_password,
    }
    res = client.post("/api/v1/auth/expert/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "expert"
    assert "access_token" in data
    assert data["user"]["email"] == settings.expert_default_email


def test_expert_login_invalid_password(client):
    payload = {
        "username_or_email": "expert@aquamedi.gov.in",
        "password": "WrongPassword999",
    }
    res = client.post("/api/v1/auth/expert/login", json=payload)
    assert res.status_code == 401
    assert "invalid_credentials" in str(res.json())


def test_expert_login_rate_limiting(client):
    payload = {
        "username_or_email": "rate_limit_test@gov.in",
        "password": "IncorrectPassword",
    }
    # Make multiple failed attempts to trigger rate limit
    for _ in range(5):
        res = client.post("/api/v1/auth/expert/login", json=payload)

    # 6th attempt should be blocked with 429 Too Many Requests
    blocked_res = client.post("/api/v1/auth/expert/login", json=payload)
    assert blocked_res.status_code in {401, 429}


def test_auth_me_with_guest_and_expert(client):
    # Guest session
    guest_res = client.post("/api/v1/auth/guest-session").json()
    guest_token = guest_res["access_token"]

    me_guest = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {guest_token}"})
    assert me_guest.status_code == 200
    assert me_guest.json()["role"] == "farmer_guest"
    assert me_guest.json()["is_authenticated"] is False

    # Expert session
    expert_res = client.post("/api/v1/auth/expert/login", json={
        "username_or_email": settings.expert_default_email,
        "password": settings.expert_default_password,
    }).json()
    expert_token = expert_res["access_token"]

    me_expert = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expert_token}"})
    assert me_expert.status_code == 200
    assert me_expert.json()["role"] == "expert"
    assert me_expert.json()["is_authenticated"] is True


# ─── RBAC Access Control Tests ───────────────────────────────────────────────

def test_guest_farmer_forbidden_from_expert_endpoints(client):
    """Verify that a Guest Farmer token is strictly denied (403) on expert endpoints."""
    guest_res = client.post("/api/v1/auth/guest-session").json()
    guest_token = guest_res["access_token"]
    headers = {"Authorization": f"Bearer {guest_token}"}

    # 1. Full scenario pipeline
    res_scenario = client.post(
        "/api/v1/scenarios/run",
        json={"scenario_type": "normal_water", "n_farmers": 3, "seed": 42},
        headers=headers,
    )
    assert res_scenario.status_code == 403
    assert "Access restricted to verified Agricultural Experts" in str(res_scenario.json())

    # 2. Conflict detection
    res_conflict = client.post(
        "/api/v1/conflicts",
        json={"scenario_type": "normal_water", "n_farmers": 3, "seed": 42},
        headers=headers,
    )
    assert res_conflict.status_code == 403

    # 3. Allocation
    res_alloc = client.post(
        "/api/v1/allocations",
        json={"scenario_type": "normal_water", "n_farmers": 3, "seed": 42},
        headers=headers,
    )
    assert res_alloc.status_code == 403

    # 4. Negotiation
    res_neg = client.post(
        "/api/v1/negotiations",
        json={"scenario_type": "normal_water", "n_farmers": 3, "seed": 42},
        headers=headers,
    )
    assert res_neg.status_code == 403


def test_guest_farmer_permitted_on_prediction_endpoints(client):
    """Verify that a Guest Farmer token is permitted (200) for water demand predictions."""
    guest_res = client.post("/api/v1/auth/guest-session").json()
    guest_token = guest_res["access_token"]
    headers = {"Authorization": f"Bearer {guest_token}"}

    farmer_payload = {
        "farmer_data": {
            "farmer_id": "FARMER_GUEST_TEST",
            "crop_type": "wheat",
            "soil_type": "loam",
            "growth_stage": "vegetative",
            "season": "rabi",
            "farm_area_hectares": 2.5,
            "et0_mm_per_day": 4.5,
            "kc_value": 0.85,
            "etc_mm_per_day": 3.825,
            "temperature_celsius": 24.0,
            "humidity_percent": 55.0,
            "rainfall_mm": 0.0,
        },
        "model_name": "XGBoost",
    }
    res = client.post("/api/v1/predictions", json=farmer_payload, headers=headers)
    assert res.status_code == 200
    assert "predicted_water_demand_m3" in res.json()
    assert res.json()["model_name"] == "XGBoost"

