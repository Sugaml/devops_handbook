#!/usr/bin/env python3
"""Print a deployment banner — Day 1 lab."""

def main() -> None:
    app = "payments-api"
    env = "staging"
    build = "a1b2c3d"
    print(f"[{env}] {app} build={build} ready for smoke tests")


if __name__ == "__main__":
    main()
