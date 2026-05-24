# SQL Handbook — Design Notes

## Goals

- Teach SQL through **DevOps-shaped data** (environments, deploys, hosts, incidents), not generic HR/orders examples.
- Standardize on **PostgreSQL 16** for labs; note MySQL deltas only when operators hit them in the wild.
- Progress from analyst-style `SELECT` to **operator responsibilities**: backups, roles, migrations, connection storms.

## Shared lab schema

| Table | Role |
|-------|------|
| `environments` | staging, production, DR |
| `services` | Logical apps (api, worker, web) |
| `hosts` | Machines or nodes tied to an environment |
| `deployments` | Release records (version, status, timestamps) |
| `incidents` | Outages linked to services |

Seed data is small (dozens of rows) so `EXPLAIN` and joins stay readable. Days 4–5 labs extend schema with `deployment_steps` and audit columns.

## Engine choice

PostgreSQL: JSONB, `RETURNING`, window functions, mature `EXPLAIN`, common on RDS and Kubernetes (CloudNativePG, Zalando). MySQL remains common for legacy apps—Day 9 and Day 12 call out syntax differences briefly.

## Edge cases documented in curriculum

- `NULL` breaks `=`, `NOT IN` with NULLs, `COUNT(*)` vs `COUNT(col)`.
- `UPDATE`/`DELETE` without `WHERE` — lab uses transactions + rollback.
- Time zones: store `timestamptz`, display in UTC in runbooks.
- `SERIAL` vs `GENERATED ALWAYS AS IDENTITY` — Day 5 prefers identity columns.
- Long migrations: lock duration, `CONCURRENTLY` for indexes (Day 9 stretch).

## Performance notes

- Labs run on empty-ish DB; real slowness needs volume—Day 9 suggests `generate_series` stretch.
- Connection pooling (PgBouncer) required before high pod count × threads (Day 15).

## User feedback / revisions

- Initial 15-day track: single-week intensive or three-week part-time.
- Future days 16–30 (optional): replication lag drills, logical decoding, Timescale/metrics, cross-region failover.
