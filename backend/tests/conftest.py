"""
AquaMediAI — pytest fixtures and configuration.

Sets PYTHONPATH so tests can import from backend/app without installation.
"""

import os
import sys
from pathlib import Path

import pytest

# ── Add backend/ to sys.path so `import app.xxx` works ───────────────────────
BACKEND_DIR = Path(__file__).parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ── Ensure test environment variables are set (no real DB needed for unit tests)
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://test:test@localhost:5432/test_aquamedi",
)
os.environ.setdefault("RANDOM_SEED", "42")
os.environ.setdefault("MODEL_DIR", "data/models")
os.environ.setdefault("DATA_DIR", "data/raw")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_pytest_only")


@pytest.fixture(scope="session")
def default_seed() -> int:
    """Return the default random seed for test reproducibility."""
    return 42


@pytest.fixture(scope="session")
def small_dataset(default_seed):
    """Generate a small synthetic dataset for fast unit testing."""
    from app.ml.data_generator import SyntheticDataGenerator

    gen = SyntheticDataGenerator(seed=default_seed)
    return gen.generate_dataset(n_samples=400)


@pytest.fixture(scope="session")
def large_dataset(default_seed):
    """Generate a larger synthetic dataset for integration-level tests."""
    from app.ml.data_generator import SyntheticDataGenerator

    gen = SyntheticDataGenerator(seed=default_seed)
    return gen.generate_dataset(n_samples=2000)
