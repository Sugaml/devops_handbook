#!/usr/bin/env python3
"""Run Ansible playbooks from Python with structured exit codes."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_extra_vars(pairs: list[str]) -> list[str]:
    args: list[str] = []
    for pair in pairs:
        args.extend(["-e", pair])
    return args


def run_playbook(
    playbook: Path,
    inventory: Path,
    *,
    check: bool = False,
    limit: str | None = None,
    extra_vars: list[str] | None = None,
) -> int:
    cmd = [
        "ansible-playbook",
        str(playbook),
        "-i",
        str(inventory),
    ]
    if check:
        cmd.append("--check")
    if limit:
        cmd.extend(["--limit", limit])
    if extra_vars:
        cmd.extend(parse_extra_vars(extra_vars))

    print(f"Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True)
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ansible playbooks from Python")
    parser.add_argument("--playbook", type=Path, required=True)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path(__file__).parent / "dynamic_inventory.py",
    )
    parser.add_argument("--check", action="store_true", help="Dry run")
    parser.add_argument("--limit", help="Host pattern limit")
    parser.add_argument(
        "--extra-var",
        action="append",
        dest="extra_vars",
        default=[],
        metavar="KEY=VALUE",
    )
    args = parser.parse_args()

    if not args.playbook.exists():
        print(f"Playbook not found: {args.playbook}", file=sys.stderr)
        sys.exit(2)

    rc = run_playbook(
        args.playbook,
        args.inventory,
        check=args.check,
        limit=args.limit,
        extra_vars=args.extra_vars,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
