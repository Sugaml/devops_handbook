"""Intentionally insecure patterns for bandit lab — DO NOT use in production."""
from __future__ import annotations

import hashlib
import pickle
import subprocess


def run_command(user_input: str) -> int:
    # B602: subprocess with shell=True — command injection risk
    return subprocess.call(f"echo {user_input}", shell=True)


def verify_password(candidate: str) -> bool:
    # B105: hardcoded password
    admin_password = "super-secret-admin-123"
    return candidate == admin_password


def load_job_state(path: str) -> dict:
    # B301: pickle load from file — arbitrary code execution
    with open(path, "rb") as fh:
        return pickle.load(fh)


def hash_token(token: str) -> str:
    # B324: weak hash for security-sensitive data
    return hashlib.md5(token.encode()).hexdigest()
