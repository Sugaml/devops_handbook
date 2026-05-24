#!/usr/bin/env python3
"""Timezone-aware scheduling and maintenance window checks."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def _field_match(field: str, value: int, min_val: int, max_val: int) -> bool:
    if field == "*":
        return True
    if field.startswith("*/"):
        step = int(field[2:])
        return value % step == 0
    if "," in field:
        return value in {int(x) for x in field.split(",")}
    return value == int(field)


def cron_match(expr: str, now: datetime) -> bool:
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError("cron expression must have 5 fields: min hour dom month dow")
    minute, hour, dom, month, dow = parts
    return (
        _field_match(minute, now.minute, 0, 59)
        and _field_match(hour, now.hour, 0, 23)
        and _field_match(dom, now.day, 1, 31)
        and _field_match(month, now.month, 1, 12)
        and _field_match(dow, now.weekday(), 0, 6)
    )


def in_maintenance_window(now: datetime, start: time, end: time, tz_name: str) -> bool:
    tz = ZoneInfo(tz_name)
    local = now.astimezone(tz)
    current = local.time()
    if start <= end:
        return start <= current < end
    return current >= start or current < end


def days_until_expiry(expires_at: datetime) -> int:
    if expires_at.tzinfo is None:
        raise ValueError("expires_at must be timezone-aware")
    return (expires_at - datetime.now(timezone.utc)).days


def events_in_last_hours(events: list[dict], hours: int = 24) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    for event in events:
        ts = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        if ts >= cutoff:
            recent.append(event)
    return recent


def main() -> int:
    parser = argparse.ArgumentParser(description="Schedule checker lab")
    parser.add_argument("command", nargs="?", default="now", choices=["now", "events"])
    parser.add_argument("--tz", default="UTC", help="Timezone for display")
    parser.add_argument("--window", nargs=2, metavar=("START", "END"), help="HH:MM HH:MM")
    parser.add_argument("--cron", metavar="EXPR", help='5-field cron e.g. "*/15 * * * *"')
    parser.add_argument("--cert-expiry", metavar="ISO8601", help="Certificate expiry timestamp")
    parser.add_argument("--events", type=Path, help="JSON file of timestamped events")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)

    if args.command == "now":
        local = now.astimezone(ZoneInfo(args.tz))
        print(
            json.dumps(
                {
                    "utc": now.isoformat(),
                    "local": local.isoformat(),
                    "epoch": int(now.timestamp()),
                },
                indent=2,
            )
        )

    if args.window:
        start = time.fromisoformat(args.window[0])
        end = time.fromisoformat(args.window[1])
        in_window = in_maintenance_window(now, start, end, args.tz)
        print(json.dumps({"maintenance_window": in_window, "timezone": args.tz}, indent=2))

    if args.cron:
        match = cron_match(args.cron, now.astimezone(ZoneInfo("UTC")))
        print(json.dumps({"cron": args.cron, "matches_now": match}, indent=2))

    if args.cert_expiry:
        expiry = datetime.fromisoformat(args.cert_expiry.replace("Z", "+00:00"))
        days = days_until_expiry(expiry)
        alert = 0 <= days <= 30
        print(json.dumps({"days_until_expiry": days, "alert": alert}, indent=2))

    if args.events:
        data = json.loads(args.events.read_text(encoding="utf-8"))
        recent = events_in_last_hours(data.get("events", []))
        print(json.dumps({"recent_events": recent}, indent=2, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
