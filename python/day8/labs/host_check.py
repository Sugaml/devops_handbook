#!/usr/bin/env python3
"""Sample ops CLI with argparse — Day 8 lab."""

import argparse
import sys


def check_host(host: str, *, dry_run: bool, fail_host: str | None) -> bool:
    if dry_run:
        print(f"[dry-run] would check {host}")
        return True
    if fail_host and host == fail_host:
        print(f"FAIL {host}", file=sys.stderr)
        return False
    print(f"OK {host}")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="host-check",
        description="Simulate host reachability checks for handbook lab",
        epilog="Example: host-check.py --env staging web1 10.0.0.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("hosts", nargs="+", help="Hostnames or IPs")
    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="staging",
        help="Target environment label",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="Probe timeout seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print plan only")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--fail-host",
        help="Simulate failure for one host (lab only)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.verbose:
        print(f"env={args.env} timeout={args.timeout}")
    results = [
        check_host(h, dry_run=args.dry_run, fail_host=args.fail_host) for h in args.hosts
    ]
    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
