# Day 15 — Production Operations: Pooling, Replicas & Monitoring

**Goal:** Operate PostgreSQL in production—connection pooling with PgBouncer, read replicas for reporting, key metrics and alerts, incident runbooks, and secrets rotation without downtime.

**Time:** 5–6 hours

---

## 1. Production architecture

```
                    ┌─────────────┐
  Apps / Jobs ─────►│  PgBouncer  │─────► Primary (read/write)
                    └─────────────┘              │
                           │                     ├── synchronous standby (optional)
                           └────────────────────► Read replica(s)
 Grafana / on-call ─────────────────────────────► (SELECT only)
```

Never point 500 Kubernetes pods directly at Postgres max_connections=100.

---

## 2. Connection pooling (PgBouncer)

**Transaction pooling** (common for web apps):

```ini
; pgbouncer.ini excerpt
[databases]
handbook = host=db port=5432 dbname=handbook

[pgbouncer]
listen_port = 6432
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

App connection string:

```
postgresql://app:***@pgbouncer:6432/handbook
```

Rules:

- No session-level features across transactions (`SET`, temp tables, `LISTEN`)
- Migrations bypass pooler → connect to primary directly

Lab: run PgBouncer in compose (stretch) or read config in `day15/labs/pgbouncer.ini`.

---

## 3. Read replicas

| Workload | Target |
|----------|--------|
| OLTP writes | Primary |
| Dashboards, analytics | Replica |
| `pg_dump` heavy reports | Replica |

Lag monitoring:

```sql
-- On primary (PostgreSQL 16+)
SELECT * FROM pg_stat_replication;

-- On replica
SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;
```

Route ORM read-only queries to replica URL; accept ** eventual consistency**.

---

## 4. Key metrics to alert on

| Metric | Warning sign |
|--------|--------------|
| `connections` / `max_connections` | Pool exhaustion |
| Replication lag | Stale reads, failover risk |
| Disk usage | WAL bloat, no autovacuum |
| `pg_stat_statements` total_time | New slow query |
| Deadlocks rate | App lock ordering bug |
| Checkpointer / WAL rate | Spike during bulk load |

RDS CloudWatch: `DatabaseConnections`, `FreeStorageSpace`, `ReplicaLag`.

---

## 5. pg_stat_statements

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

SELECT
    calls,
    round(total_exec_time::numeric, 2) AS total_ms,
    round(mean_exec_time::numeric, 2) AS mean_ms,
    left(query, 80) AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

Reset after deploy to compare regressions:

```sql
SELECT pg_stat_statements_reset();
```

---

## 6. Incident runbook snippets

**Kill runaway query:**

```sql
SELECT pg_cancel_backend(pid);   -- gentle
SELECT pg_terminate_backend(pid);  -- force
FROM pg_stat_activity WHERE pid = 12345;
```

**Failover (managed):** promote replica via cloud console—update DNS/secret endpoint.

**Disk full:** expand volume, `VACUUM` (not FULL in panic unless needed), archive WAL.

---

## 7. Secrets rotation

1. Create `app_v2` role with same grants.
2. Deploy apps with dual-secret support or rolling update to `app_v2`.
3. Revoke `app_v1` after all pods healthy.

Use IAM database auth on RDS to avoid static passwords entirely.

---

## 8. Health checks

**Liveness** (app): `SELECT 1`

**Deep check** (synthetic): insert + delete heartbeat row or verify migration version:

```sql
SELECT version, description, installed_on
FROM flyway_schema_history
ORDER BY installed_rank DESC
LIMIT 1;
```

---

## 9. Lab — Day 15

From `sql/day15/labs/`:

1. Run `monitoring_queries.sql`; interpret `pg_stat_activity`.
2. Simulate connection pressure: open 10 `psql` sessions; watch count in monitoring query.
3. Enable `pg_stat_statements` in lab (may need `shared_preload_libraries` — document limitation in Docker).
4. Write alert thresholds for connections > 80%, lag > 30s, disk > 85%.
5. Draft one-page runbook: "Payments DB connections maxed out" — diagnosis + mitigation steps.
6. Map handbook topics to your stack (RDS vs self-hosted K8s operator).

**Stretch:** Add PgBouncer service to `docker-compose.yml` and connect through port 6432.

---

## 10. DevOps connections — capstone

| Day | Production tie-in |
|-----|-------------------|
| 1–4 | On-call ad-hoc queries |
| 5–8 | Schema + reports |
| 9 | Slow query firefighting |
| 10 | Safe concurrent deploy scripts |
| 11 | Design reviews |
| 12 | IAM + least privilege |
| 13 | Restore drills (mandatory quarterly) |
| 14 | CI migration gate |
| 15 | SLOs, pooling, replicas |

You now have the SQL foundation to pair with [AWS RDS Day 17](../../aws/day17/), application deploy pipelines ([CI/CD handbook](../../cicd/README.md)), and Kubernetes stateful workloads ([Kubernetes Day 11](../../kubernetes/day11/)).

---

## Quick reference

| Task | Command / query |
|------|-------------------|
| Active queries | `pg_stat_activity` |
| Slow queries | `pg_stat_statements` |
| Replication lag | `pg_stat_replication` |
| Pooling | PgBouncer transaction mode |
| Health | `SELECT 1` |
| Cancel query | `pg_cancel_backend(pid)` |

**Handbook complete.** Revisit any day with the shared lab schema; consider Days 16+ for logical replication and multi-region in [DESIGN.md](../DESIGN.md).
