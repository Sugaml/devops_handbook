#!/usr/bin/env python3
"""Disk usage and largest Python files under a path — Day 10 lab."""

import shutil
import sys
from pathlib import Path


def disk_summary(path: Path) -> None:
    usage = shutil.disk_usage(path)
    gib = 2**30
    print(f"path={path}")
    print(f"  total_gib={usage.total / gib:.2f}")
    print(f"  used_gib={usage.used / gib:.2f}")
    print(f"  free_gib={usage.free / gib:.2f}")


def largest_py_files(root: Path, limit: int = 5) -> list[tuple[int, Path]]:
    files: list[tuple[int, Path]] = []
    for p in root.rglob("*.py"):
        if p.is_file():
            files.append((p.stat().st_size, p))
    files.sort(reverse=True)
    return files[:limit]


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    if not target.exists():
        print(f"path does not exist: {target}", file=sys.stderr)
        sys.exit(2)
    disk_summary(target.resolve())
    print("largest .py files:")
    for size, path in largest_py_files(target):
        print(f"  {size:8}  {path.relative_to(target) if path.is_relative_to(target) else path}")


if __name__ == "__main__":
    main()
