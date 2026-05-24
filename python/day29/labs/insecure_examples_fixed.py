"""Remediated versions of insecure patterns from insecure_examples.py."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


def run_command(message: str) -> int:
    return subprocess.run(["echo", message], check=False).returncode


def verify_password(candidate: str) -> bool:
    expected = os.environ.get("ADMIN_PASSWORD", "")
    if not expected:
        raise RuntimeError("ADMIN_PASSWORD not configured")
    return candidate == expected


def load_job_state(path: Path) -> dict:
    return json.loads(path.read_text())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
