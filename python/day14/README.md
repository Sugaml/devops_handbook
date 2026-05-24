# Day 14 — datetime, Timezones & Cron-like Scheduling Patterns

**Goal:** Handle timestamps, timezones, and scheduling logic correctly in DevOps scripts — maintenance windows, backup schedules, and cron-equivalent checks without silent off-by-one-hour bugs.

**Time:** 4–5 hours (theory + hands-on)

---

## 1. Why time trips up automation

| Failure mode | Example |
|--------------|---------|
| Naive vs aware datetimes | Comparing UTC log time to local "now" |
| DST transitions | Job runs twice or skips in spring/fall |
| String parsing without TZ | `2026-05-24 09:00` — which zone? |
| Cron drift | "Run at 2am" on servers in different zones |

DevOps scripts schedule backups, certificate expiry checks, and maintenance gates. **Always store UTC; display local.**

---

## 2. Aware datetimes with zoneinfo (Python 3.9+)

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

utc_now = datetime.now(timezone.utc)
tokyo = utc_now.astimezone(ZoneInfo("Asia/Tokyo"))
print(tokyo.isoformat())  # 2026-05-24T18:00:00+09:00
```

**Rule:** Use `datetime.now(timezone.utc)` — never `datetime.utcnow()` (naive, deprecated pattern).

---

## 3. Parsing ISO 8601 timestamps

```python
from datetime import datetime

# From API / logs
ts = datetime.fromisoformat("2026-05-24T14:30:00+00:00")

# Z suffix (common in JSON)
raw = "2026-05-24T14:30:00Z"
ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
```

For arbitrary formats, use `dateutil` (optional):

```bash
pip install python-dateutil
```

```python
from dateutil import parser
ts = parser.isoparse("2026-05-24T14:30:00+00:00")
```

---

## 4. Maintenance window checks

```python
from datetime import datetime, time
from zoneinfo import ZoneInfo

def in_maintenance_window(
    now: datetime,
    start: time,
    end: time,
    tz: ZoneInfo,
) -> bool:
    local = now.astimezone(tz)
    current = local.time()
    if start <= end:
        return start <= current < end
    # Window crosses midnight (e.g. 22:00 - 06:00)
    return current >= start or current < end
```

Use this to skip deploys during declared maintenance.

---

## 5. Cron-like scheduling without cron

For "should this job run now?" logic inside a script polled every minute:

```python
# Simplified: run at minute 0, 15, 30, 45
def should_run_quarter_hour(now: datetime) -> bool:
    return now.minute % 15 == 0 and now.second < 30

# Match cron fields: minute hour day month weekday
def cron_match(expr: str, now: datetime) -> bool:
    """Minimal 5-field matcher — see lab for full implementation."""
    minute, hour, dom, month, dow = expr.split()
    return (
        _field_match(minute, now.minute, 0, 59)
        and _field_match(hour, now.hour, 0, 23)
        and _field_match(dom, now.day, 1, 31)
        and _field_match(month, now.month, 1, 12)
        and _field_match(dow, now.weekday(), 0, 6)  # 0=Monday
    )
```

Production alternative: use **APScheduler** or system **cron** / **systemd timers** and keep Python for the job body only.

---

## 6. APScheduler for in-process scheduling

```bash
pip install apscheduler
```

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timezone

def backup_job():
    print(f"Backup at {datetime.now(timezone.utc).isoformat()}")

scheduler = BlockingScheduler(timezone="UTC")
scheduler.add_job(backup_job, "cron", hour=2, minute=0)
scheduler.start()
```

Prefer external schedulers (cron, K8s CronJob) for production reliability — APScheduler dies when the process exits.

---

## 7. Certificate and resource expiry

```python
from datetime import datetime, timedelta, timezone

def days_until_expiry(expires_at: datetime) -> int:
    if expires_at.tzinfo is None:
        raise ValueError("expires_at must be timezone-aware")
    delta = expires_at - datetime.now(timezone.utc)
    return delta.days

def alert_if_expiring_soon(expires_at: datetime, threshold_days: int = 30) -> bool:
    return 0 <= days_until_expiry(expires_at) <= threshold_days
```

TLS cert monitors and IAM key rotation scripts use this pattern daily.

---

## 8. Formatting for logs and reports

```python
# Human-readable UTC in logs
stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Unix epoch for metrics
epoch = int(datetime.now(timezone.utc).timestamp())
```

Never mix formats in the same log pipeline without documenting the standard.

---

## 9. Lab — Day 14

Work from `python/day14/labs/`.

1. Run `python schedule_checker.py now` — prints UTC and your local zone.
2. Run `python schedule_checker.py --window 22:00 06:00 --tz America/New_York` — test inside/outside maintenance window.
3. Run `python schedule_checker.py --cron "*/15 * * * *"` — confirm match at :00, :15, :30, :45.
4. Run `python schedule_checker.py --cert-expiry 2026-06-15T00:00:00+00:00` — days remaining and alert flag.
5. Feed `sample_events.json` timestamps; script reports which events fall in last 24h UTC.

**Stretch:** Add `--dry-run-schedule` that prints next 5 run times for a cron expression.

---

## 10. DevOps connections

- **Kubernetes CronJob:** `schedule: "0 2 * * *"` is UTC in the API unless documented otherwise — align Python checks.
- **CloudWatch / log aggregation:** Normalize to UTC at ingest; convert only in dashboards.
- **Incident timelines:** Post-mortems require explicit timezone on every timestamp.

---

## Quick reference

| Task | Code |
|------|------|
| UTC now (aware) | `datetime.now(timezone.utc)` |
| Convert zone | `.astimezone(ZoneInfo("Europe/London"))` |
| Parse ISO | `datetime.fromisoformat(s.replace("Z", "+00:00"))` |
| Epoch seconds | `int(dt.timestamp())` |
| Cron in K8s | Prefer CronJob; Python for job logic |

**Next:** [Day 15 — boto3 AWS automation (EC2, S3, STS)](../day15/)
