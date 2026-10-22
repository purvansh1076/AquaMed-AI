"""
AquaMediAI — Database Engine & Session
=======================================
Synchronous SQLAlchemy 2.x setup.

Rationale: Synchronous sessions are simpler for the academic MVP and avoid
the complexity of async context management. The architecture can be migrated
to async (asyncpg + create_async_engine) by swapping engine creation and
replacing ``Session`` with ``AsyncSession`` without touching business logic.
"""

from __future__ import annotations

import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)


# ─── Declarative Base ─────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    Shared SQLAlchemy declarative base.
    All ORM models inherit from this class.
    """
    pass


# ─── Engine ───────────────────────────────────────────────────────────────────

def _create_db_engine():
    """Create and return the SQLAlchemy synchronous engine."""
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,        # Detect stale connections
        pool_size=5,               # Connection pool size
        max_overflow=10,           # Extra connections under load
        echo=settings.app_debug,  # Log SQL in debug mode
    )
    logger.info("Database engine created for: %s", settings.database_url.split("@")[-1])
    return engine


engine = _create_db_engine()

# ─── Session Factory ──────────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevent "DetachedInstanceError" after commit
)


# ─── FastAPI Dependency ────────────────────────────────────────────────────────

def get_db() -> Session:
    """
    FastAPI dependency that yields a database session per request.

    Usage::

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ─── Health-check helper ───────────────────────────────────────────────────────

def check_db_connection() -> bool:
    """
    Verify the database is reachable.
    Returns True on success, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Database connection check failed: %s", exc)
        return False
