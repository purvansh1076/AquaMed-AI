"""
AquaMediAI — Root ASGI Application Entry Point
==============================================
Exposes the FastAPI application instance from `app.main`.
Allows running:
    python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
directly from the backend/ directory without setting PYTHONPATH.
"""

from app.main import app

__all__ = ["app"]
