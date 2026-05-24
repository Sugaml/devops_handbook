#!/usr/bin/env python3
"""Git repository audit lab using GitPython."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError


SENSITIVE_PATHS = (".env", "secrets/", "credentials.json", ".pem")


def open_repo(path: Path) -> Repo:
    try:
        return Repo(path)
    except InvalidGitRepositoryError as exc:
        raise SystemExit(f"ERROR: not a git repo: {path}") from exc


def cmd_summary(repo: Repo) -> dict:
    head = repo.head.commit
    return {
        "path": str(repo.working_tree_dir),
        "branch": repo.active_branch.name,
        "head": head.hexsha,
        "author": f"{head.author.name} <{head.author.email}>",
        "date": head.committed_datetime.isoformat(),
        "message": head.summary,
    }


def cmd_log(repo: Repo, count: int) -> list[dict]:
    rows = []
    for c in repo.iter_commits(max_count=count):
        rows.append(
            {
                "sha": c.hexsha[:8],
                "author": c.author.email,
                "date": c.committed_datetime.isoformat(),
                "message": c.summary,
            }
        )
    return rows


def cmd_stale_branches(repo: Repo, days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stale = []
    for branch in repo.branches:
        committed = branch.commit.committed_datetime
        if committed.tzinfo is None:
            committed = committed.replace(tzinfo=timezone.utc)
        if committed < cutoff:
            stale.append(
                {
                    "branch": branch.name,
                    "last_commit": committed.isoformat(),
                    "sha": branch.commit.hexsha[:8],
                }
            )
    return stale


def cmd_sensitive_diff(repo: Repo, base: str) -> dict:
    commit = repo.head.commit
    try:
        parent = repo.commit(base)
    except Exception as exc:
        raise SystemExit(f"ERROR: invalid base ref {base!r}: {exc}") from exc
    hits = []
    for d in parent.diff(commit):
        path = d.b_path or d.a_path or ""
        if any(s in path for s in SENSITIVE_PATHS):
            hits.append({"change_type": d.change_type, "path": path})
    return {"base": base, "head": commit.hexsha[:8], "sensitive_hits": hits}


def main() -> int:
    parser = argparse.ArgumentParser(description="Git audit lab")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary", help="Repo summary")
    p_log = sub.add_parser("log", help="Recent commits")
    p_log.add_argument("--count", type=int, default=10)
    p_stale = sub.add_parser("stale-branches", help="Branches older than N days")
    p_stale.add_argument("--days", type=int, default=90)
    p_diff = sub.add_parser("sensitive-diff", help="Flag sensitive paths in diff")
    p_diff.add_argument("--base", default="HEAD~1")

    args = parser.parse_args()
    repo = open_repo(args.repo.resolve())

    if args.command == "summary":
        print(json.dumps(cmd_summary(repo), indent=2))
    elif args.command == "log":
        print(json.dumps({"commits": cmd_log(repo, args.count)}, indent=2))
    elif args.command == "stale-branches":
        print(json.dumps({"stale": cmd_stale_branches(repo, args.days)}, indent=2))
    else:
        result = cmd_sensitive_diff(repo, args.base)
        print(json.dumps(result, indent=2))
        return 1 if result["sensitive_hits"] else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
