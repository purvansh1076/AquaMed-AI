"""
AquaMediAI — Application Configuration
=======================================
Reads all settings from environment variables (or a .env file).
Uses pydantic-settings for validation and type coercion.

NEVER hard-code secrets here. Use .env (git-ignored).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Central configuration object loaded from environment variables.
    All fields have safe defaults for local development; override via .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+psycopg2://aquamedi:aquamedi_secret@localhost:5432/aquamedi_db"
    )

    # ── CORS ───────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list of strings, including 127.0.0.1 equivalents."""
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        expanded: List[str] = list(origins)
        for o in origins:
            if "localhost" in o:
                alt = o.replace("localhost", "127.0.0.1")
                if alt not in expanded:
                    expanded.append(alt)
            elif "127.0.0.1" in o:
                alt = o.replace("127.0.0.1", "localhost")
                if alt not in expanded:
                    expanded.append(alt)
        return expanded

    # ── ML / Data ──────────────────────────────────────────────────────────────
    random_seed: int = 42
    model_dir: str = "data/models"
    data_dir: str = "data/raw"
    enable_shadow_mode: bool = True
    enable_candidate_v3_shadow: bool = False
    candidate_v3_dir: str = "data/models/candidate_v3"

    # ── Logging ────────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Derived helpers ────────────────────────────────────────────────────────
    @property
    def model_dir_path(self) -> Path:
        """Absolute Path to the model artifact directory."""
        raw_path = Path(self.model_dir)
        if raw_path.is_absolute():
            return raw_path.resolve()

        # Check candidate locations:
        # 1. Relative to CWD (e.g., when executed inside backend/)
        cwd_candidate = (Path.cwd() / raw_path).resolve()
        if (cwd_candidate / "encoders.joblib").exists() or (cwd_candidate / "rf_model.joblib").exists():
            return cwd_candidate

        # 2. Relative to BACKEND_DIR (e.g., when executed from repository root or external directories)
        backend_candidate = (BACKEND_DIR / raw_path).resolve()
        if (backend_candidate / "encoders.joblib").exists() or (backend_candidate / "rf_model.joblib").exists():
            return backend_candidate

        # Fallback to existing directory if present, else backend_candidate
        if cwd_candidate.exists():
            return cwd_candidate
        return backend_candidate

    @property
    def candidate_v3_dir_path(self) -> Path:
        """Absolute Path to Candidate v3 artifacts."""
        raw_path = Path(self.candidate_v3_dir)
        if raw_path.is_absolute():
            return raw_path.resolve()

        cwd_candidate = (Path.cwd() / raw_path).resolve()
        if (cwd_candidate / "two_stage_config.json").exists():
            return cwd_candidate

        backend_candidate = (BACKEND_DIR / raw_path).resolve()
        if (backend_candidate / "two_stage_config.json").exists():
            return backend_candidate

        if cwd_candidate.exists():
            return cwd_candidate
        return backend_candidate

    @property
    def data_dir_path(self) -> Path:
        """Absolute Path to the raw data directory."""
        raw_path = Path(self.data_dir)
        if raw_path.is_absolute():
            return raw_path.resolve()

        cwd_candidate = (Path.cwd() / raw_path).resolve()
        if cwd_candidate.exists():
            return cwd_candidate

        backend_candidate = (BACKEND_DIR / raw_path).resolve()
        return backend_candidate

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got '{v}'")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v_upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached Settings singleton.

    Uses lru_cache so the .env file is parsed only once per process.
    In tests, call ``get_settings.cache_clear()`` after patching env vars.
    """
    return Settings()
