#!/usr/bin/env python3
"""Summarize ERROR/WARN lines in a sample app log — Day 5 lab."""

from collections import Counter
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "sample_app.log"


def summarize(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if " ERROR " in line:
                counts["ERROR"] += 1
            elif " WARN " in line:
                counts["WARN"] += 1
    return counts


def main() -> None:
    if not LOG_PATH.exists():
        raise SystemExit(f"missing log: {LOG_PATH}")
    counts = summarize(LOG_PATH)
    print(f"file={LOG_PATH.name}")
    for level, n in counts.most_common():
        print(f"  {level}: {n}")


if __name__ == "__main__":
    main()
