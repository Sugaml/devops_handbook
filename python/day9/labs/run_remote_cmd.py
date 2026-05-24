#!/usr/bin/env python3
"""Run a command via argv list (simulated remote) — Day 9 lab."""

import argparse
import shlex
import subprocess
import sys


def run_command(argv: list[str], *, dry_run: bool, timeout: float | None) -> int:
    print("exec:", shlex.join(argv))
    if dry_run:
        return 0
    try:
        result = subprocess.run(
            argv,
            check=True,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or exc.stdout or "", file=sys.stderr)
        return exc.returncode
    except subprocess.TimeoutExpired:
        print("command timed out", file=sys.stderr)
        return 124
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute a local command safely (lab)")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command after -- e.g. -- echo hello",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.command:
        print("provide a command after --", file=sys.stderr)
        sys.exit(2)
    code = run_command(args.command, dry_run=args.dry_run, timeout=args.timeout)
    sys.exit(code)


if __name__ == "__main__":
    main()
