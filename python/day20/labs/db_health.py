#!/usr/bin/env python3
"""Database health checks — SQLite and PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

try:
    import psycopg2
    import psycopg2.errors
except ImportError:
    psycopg2 = None  # type: ignore


def sqlite_health(path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS health_probe "
            "(id INTEGER PRIMARY KEY, checked_at TEXT DEFAULT (datetime('now')))"
        )
        start = time.monotonic()
        row = conn.execute("SELECT 1").fetchone()
        latency_ms = (time.monotonic() - start) * 1000
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.commit()
        ok = row[0] == 1 and integrity == "ok"
        return {
            "database": "sqlite",
            "path": str(path),
            "ok": ok,
            "latency_ms": round(latency_ms, 2),
            "integrity": integrity,
        }
    finally:
        conn.close()


def postgres_health(dsn: str, expect_table: str | None, max_latency_ms: float | None) -> dict:
    if psycopg2 is None:
        return {"database": "postgresql", "ok": False, "error": "pip install psycopg2-binary"}
    try:
        conn = psycopg2.connect(dsn, connect_timeout=5)
    except psycopg2.Error as exc:
        return {"database": "postgresql", "ok": False, "error": str(exc)}

    try:
        start = time.monotonic()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            ping = cur.fetchone()[0]
        latency_ms = (time.monotonic() - start) * 1000

        table_ok = True
        if expect_table:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXISTS (
                      SELECT 1 FROM information_schema.tables
                      WHERE table_schema = 'public' AND table_name = %s
                    )
                    """,
                    (expect_table,),
                )
                table_ok = bool(cur.fetchone()[0])

        ok = ping == 1 and table_ok
        if max_latency_ms is not None and latency_ms > max_latency_ms:
            ok = False

        return {
            "database": "postgresql",
            "ok": ok,
            "latency_ms": round(latency_ms, 2),
            "expect_table": expect_table,
            "table_ok": table_ok,
        }
    except psycopg2.Error as exc:
        return {"database": "postgresql", "ok": False, "error": str(exc)}
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Database health lab")
    parser.add_argument("--max-latency-ms", type=float, help="Fail if latency exceeds threshold")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sqlite = sub.add_parser("sqlite", help="SQLite health check")
    p_sqlite.add_argument("--path", type=Path, default=Path("/tmp/handbook.db"))

    p_pg = sub.add_parser("postgres", help="PostgreSQL health check")
    p_pg.add_argument("--dsn", default=os.environ.get("DATABASE_URL"))
    p_pg.add_argument("--expect-table", help="Require table to exist in public schema")

    args = parser.parse_args()

    if args.command == "sqlite":
        report = sqlite_health(args.path)
    else:
        if not args.dsn:
            print("ERROR: set DATABASE_URL or pass --dsn", file=sys.stderr)
            return 1
        report = postgres_health(args.dsn, args.expect_table, args.max_latency_ms)

    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
