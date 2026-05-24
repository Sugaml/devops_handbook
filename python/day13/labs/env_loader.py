#!/usr/bin/env python3
"""Environment variable loader with secrets hygiene patterns."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

SENSITIVE_SUBSTRINGS = ("password", "secret", "token", "api_key", "credential")
LOG_SECRET_PATTERN = re.compile(
    r"(api[_-]?key|password|secret|token)\s*[=:]\s*\S+",
    re.IGNORECASE,
)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable not set: {name}")
    return value


def redact(value: str, visible: int = 4) -> str:
    if len(value) <= visible:
        return "****"
    return value[:visible] + "****"


@dataclass(frozen=True)
class Settings:
    api_key: str
    database_url: str
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            api_key=require_env("API_KEY"),
            database_url=require_env("DATABASE_URL"),
            log_level=os.getenv("LOG_LEVEL", "info"),
        )

    def display(self) -> dict[str, str]:
        return {
            "api_key": redact(self.api_key),
            "database_url": redact(self.database_url.split("@")[-1]),
            "log_level": self.log_level,
        }


def audit_environ() -> list[str]:
    findings: list[str] = []
    for name, value in sorted(os.environ.items()):
        lower = name.lower()
        if any(s in lower for s in SENSITIVE_SUBSTRINGS):
            findings.append(f"{name}={redact(value)}")
    return findings


def scan_log_for_secrets(path: Path) -> list[str]:
    hits: list[str] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if LOG_SECRET_PATTERN.search(line):
            hits.append(f"line {i}: possible secret in log")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Env loader lab")
    parser.add_argument("--env-file", type=Path, default=Path(__file__).parent / ".env")
    parser.add_argument("--audit", action="store_true", help="Audit sensitive env vars")
    parser.add_argument("--check-logs", type=Path, metavar="FILE", help="Scan log for secrets")
    args = parser.parse_args()

    if args.check_logs:
        hits = scan_log_for_secrets(args.check_logs)
        if hits:
            for hit in hits:
                print(f"WARN: {hit}", file=sys.stderr)
            return 1
        print("No secrets detected in log.")
        return 0

    if args.env_file.exists():
        load_dotenv(args.env_file, override=False)
    else:
        print(f"Note: {args.env_file} not found; using existing environment only.", file=sys.stderr)

    if args.audit:
        for line in audit_environ():
            print(line)
        return 0

    try:
        settings = Settings.from_env()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    import json

    print(json.dumps(settings.display(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
