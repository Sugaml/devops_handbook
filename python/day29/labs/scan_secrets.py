#!/usr/bin/env python3
"""Scan files for likely secrets before commit."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key ID"),
    (re.compile(r"(?i)(password|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]"), "hardcoded credential"),
    (re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"), "private key block"),
]


def scan_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        return findings
    for pattern, label in PATTERNS:
        if pattern.search(text):
            findings.append(f"{path}: possible {label}")
    return findings


def scan_tree(root: Path) -> list[str]:
    results: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".yaml", ".yml", ".env", ".json", ".toml"}:
            if ".venv" in path.parts or "__pycache__" in path.parts:
                continue
            results.extend(scan_file(path))
    return results


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    findings = scan_tree(root)
    if findings:
        print("\n".join(findings))
        sys.exit(1)
    print(f"No secret patterns found under {root}")


if __name__ == "__main__":
    main()
