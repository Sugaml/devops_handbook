"""Shared pytest fixtures."""
from __future__ import annotations

import pytest


@pytest.fixture
def sample_targets() -> list[dict]:
    return [
        {"name": "ok", "url": "https://example.com", "expected_status": 200},
    ]
