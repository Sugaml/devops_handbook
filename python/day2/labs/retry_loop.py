#!/usr/bin/env python3
"""Simulate deploy retries with backoff — Day 2 lab."""

import random
import time

MAX_ATTEMPTS = 5
BACKOFF_SEC = 1.0


def attempt_deploy() -> bool:
    """Pretend deploy; ~40% success."""
    return random.random() < 0.4


def main() -> None:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"attempt {attempt}/{MAX_ATTEMPTS}")
        success = attempt_deploy()
        if success:
            print("deploy succeeded")
            break
        wait = BACKOFF_SEC * attempt
        print(f"failed — sleeping {wait:.1f}s")
        time.sleep(wait)
    else:
        print("deploy failed after all attempts", file=__import__("sys").stderr)


if __name__ == "__main__":
    main()
