"""
Dashboard backend entrypoint. Thin wrapper around src/api/main.py so the
dashboard can be deployed/run independently of the core pipeline package.
"""

from src.api.main import app  # noqa: F401

# Run with: uvicorn dashboard.backend.main:app --reload
