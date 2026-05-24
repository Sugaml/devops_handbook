# Day 20 — Database Health Checks (SQLite & PostgreSQL)

**Goal:** Build database health check scripts using SQLite (stdlib) and PostgreSQL (`psycopg2`) — connection tests, latency measurement, schema validation, and replication lag patterns for DevOps monitoring.

**Time:** 5–6 hours (theory + hands-on)

---

## 1. Database checks in DevOps

Applications expose `/health`, but operators also verify **data plane** directly:

```
  monitoring cron
       │
       ├── TCP connect + auth
       ├── simple query (SELECT 1)
       ├── latency threshold
       └── optional: replication lag, disk usage
```

| Database | Python driver | Typical deployment |
|----------|---------------|-------------------|
| **SQLite** | `sqlite3` (stdlib) | Edge, CI fixtures, local tools |
| **PostgreSQL** | `psycopg2` / `psycopg2-binary` | RDS, Cloud SQL, self-hosted |

Exit code 0/1 integrates with Nagios, Prometheus custom checks, and CI smoke tests.

---

## 2. SQLite — create and probe

```python
import sqlite3
from pathlib import Path

db_path = Path("/tmp/handbook.db")
conn = sqlite3.connect(db_path, timeout=5)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute(
    "CREATE TABLE IF NOT EXISTS health_probe (id INTEGER PRIMARY KEY, checked_at TEXT)"
)
conn.execute("INSERT INTO health_probe (checked_at) VALUES (datetime('now'))")
conn.commit()

row = conn.execute("SELECT 1").fetchone()
assert row[0] == 1
conn.close()
```

**Integrity check:**

```python
def sqlite_integrity(path: Path) -> bool:
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        return row[0] == "ok"
    finally:
        conn.close()
```

---

## 3. PostgreSQL — connect with psycopg2

```bash
pip install psycopg2-binary
# DATABASE_URL=postgresql://user:pass@localhost:5432/app
```

```python
import os
import psycopg2

def pg_connect():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def pg_ping(conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        return cur.fetchone()[0] == 1
```

Use connection string from environment (Day 13) — never hard-code passwords.

---

## 4. Latency and timeouts

```python
import time

def measure_query_ms(conn, sql: str = "SELECT 1") -> float:
    start = time.monotonic()
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.fetchone()
    return (time.monotonic() - start) * 1000
```

Alert if latency exceeds SLO (e.g. 100ms for `SELECT 1` on primary).

```python
conn = psycopg2.connect(dsn, connect_timeout=5)
```

---

## 5. Schema and migration version checks

```python
def table_exists(conn, table: str) -> bool:
    sql = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        )
    """
    with conn.cursor() as cur:
        cur.execute(sql, (table,))
        return cur.fetchone()[0]

def migration_version(conn) -> int | None:
    if not table_exists(conn, "schema_migrations"):
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(version) FROM schema_migrations")
        row = cur.fetchone()
        return row[0]
```

Fail deploy if expected migration version not applied.

---

## 6. Replication lag (PostgreSQL)

On a replica:

```python
def replication_lag_bytes(conn) -> int | None:
    sql = """
        SELECT pg_wal_lsn_diff(
            pg_last_wal_receive_lsn(),
            pg_last_wal_replay_lsn()
        )
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        row = cur.fetchone()
        return row[0] if row else None
```

Compare against threshold before promoting replica or during incident triage.

---

## 7. Connection pool note

Short health scripts open one connection per run. Long-running apps use **psycopg2.pool** or SQLAlchemy — out of scope for Day 20 probes.

Always close connections:

```python
try:
    conn = pg_connect()
    ...
finally:
    conn.close()
```

Context manager: `with psycopg2.connect(dsn) as conn:`

---

## 8. Unified health report JSON

```python
report = {
    "database": "postgresql",
    "ok": True,
    "latency_ms": 12.4,
    "migration_version": 42,
    "checks": [],
}
```

Same structure as Day 12 HTTP health — consistent tooling across stack layers.

---

## 9. Lab — Day 20

Work from `python/day20/labs/`.

1. Run `python db_health.py sqlite --path /tmp/handbook.db` — creates DB if missing, runs integrity + ping.
2. Run twice; confirm latency_ms in JSON output.
3. Start local Postgres (Docker):  
   `docker run --rm -d --name pg-lab -e POSTGRES_PASSWORD=handbook -p 5432:5432 postgres:16-alpine`
4. Export `DATABASE_URL=postgresql://postgres:handbook@localhost:5432/postgres`
5. Run `python db_health.py postgres` — connection and SELECT 1.
6. Run `python db_health.py postgres --expect-table pg_catalog.pg_class` — built-in sanity check.
7. Stop container: `docker stop pg-lab`; run postgres check — confirm exit code 1.

**Stretch:** Add `--max-latency-ms 50` flag that fails if probe exceeds threshold.

---

## 10. DevOps connections

- **Kubernetes:** App readiness may pass while DB is degraded — external probes catch RDS failover delays.
- **Migrations:** Flyway/Liquibase/Alembic apply schema; Python verifies version post-deploy.
- **Backups:** SQLite `integrity_check`; Postgres `pg_dump` verify scripts use similar connectivity patterns.

---

## Quick reference

| Task | Code |
|------|------|
| SQLite ping | `conn.execute("SELECT 1")` |
| SQLite integrity | `PRAGMA integrity_check` |
| PG connect | `psycopg2.connect(dsn, connect_timeout=5)` |
| PG ping | `SELECT 1` |
| Table exists | Query `information_schema.tables` |
| Latency | `time.monotonic()` around query |

**Next:** [Day 21 — Ansible programmatic use & dynamic inventory](../day21/)
