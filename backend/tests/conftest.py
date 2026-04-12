"""Shared pytest fixtures.

These tests run against a live backend + postgres + redis + worker-kokoro stack
(the standard dev compose), so they validate the real HTTP surface rather than
mocking at the FastAPI TestClient level. This matches the project convention of
running tests inside the running container.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI TestClient bound to the app — shares the same DB + Celery config."""
    return TestClient(app)


@pytest.fixture(scope="session")
def kokoro_available() -> bool:
    """Whether the kokoro worker is expected to be reachable (skip heavy tests if not)."""
    return os.environ.get("SKIP_KOKORO_TESTS", "").lower() not in ("1", "true", "yes")
