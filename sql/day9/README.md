# Day 9 — Indexes, EXPLAIN & Query Performance

**Goal:** Read query plans with `EXPLAIN`, choose B-tree indexes for common filters and joins, and apply basic slow-query triage used in production on-call.

**Time:** 4–5 hours

---

## 1. How PostgreSQL executes queries (simplified)

```
SQL → Parser → Planner (cost estimates) → Executor → Results
                      ↑
                 Statistics (ANALYZE)
```

The planner picks join order, index scans vs sequential scans based on **cost**, not magic.

---

## 2. EXPLAIN basics

```sql
EXPLAIN
SELECT * FROM deployments WHERE service_id = 1;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT d.version, s.name
FROM deployments d
JOIN services s ON s.id = d.service_id
WHERE d.started_at >= now() - interval '7 days';
```

| Node type | Meaning |
|-----------|---------|
| `Seq Scan` | Read whole table—OK when small |
| `Index Scan` | Use index to find rows |
| `Bitmap Index Scan` | Combine multiple indexes |
| `Nested Loop` | For each row, inner lookup |
| `Hash Join` | Build hash table on join key |

**ANALYZE** actually runs the query—use on lab data only or with `LIMIT` in dev.

Key metrics: **actual time**, **rows**, **Buffers: shared hit/read**.

---

## 3. When to index

Index columns used in:

- `WHERE` equality/range (`service_id`, `started_at`)
- `JOIN` keys (`environment_id`)
- `ORDER BY` on large sets (sometimes)

Lab schema already has:

```sql
idx_deployments_service_env
idx_deployments_started_at
idx_incidents_opened_at
```

Verify usage:

```sql
EXPLAIN ANALYZE
SELECT * FROM deployments
WHERE service_id = 1 AND environment_id = 2
ORDER BY started_at DESC
LIMIT 10;
```

---

## 4. Creating indexes

```sql
CREATE INDEX idx_deployments_status ON deployments (status);

-- Composite (column order matters)
CREATE INDEX idx_deployments_env_started ON deployments (environment_id, started_at DESC);
```

Production large tables:

```sql
CREATE INDEX CONCURRENTLY idx_name ON table (col);
-- No long exclusive lock; cannot run inside transaction block
```

---

## 5. Index trade-offs

| Pro | Con |
|-----|-----|
| Faster reads | Slower writes (INSERT/UPDATE) |
| Faster JOINs | Disk space |
| Enforces sort order sometimes | Wrong index = unused bloat |

Drop unused indexes found in monitoring:

```sql
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

---

## 6. Common slow-query patterns

**Function on indexed column prevents index use:**

```sql
-- Bad
WHERE date(started_at) = '2024-05-01'
-- Better
WHERE started_at >= '2024-05-01' AND started_at < '2024-05-02'
```

**Leading wildcard LIKE:**

```sql
WHERE hostname LIKE '%api%'   -- cannot use B-tree index
WHERE hostname LIKE 'prod-%'  -- can use index
```

**Missing stats:** run `ANALYZE deployments;`

---

## 7. Generate load for EXPLAIN (stretch)

```sql
INSERT INTO deployments (service_id, environment_id, version, status, deployed_by, started_at)
SELECT
    (random() * 3 + 1)::int,
    (random() * 2 + 1)::int,
    'bulk-' || g,
    'success',
    'loadgen',
    now() - (random() * 365 || ' days')::interval
FROM generate_series(1, 50000) g;
```

Re-run EXPLAIN before/after index—watch Seq Scan → Index Scan.

---

## 8. Lab — Day 9

From `sql/day9/labs/`:

1. `\timing on`; run `explain_deployments.sql` with and without `ANALYZE`.
2. Identify whether existing indexes appear in plan for service+env filter.
3. Create index on `deployments(status)`; re-EXPLAIN a status filter query.
4. Query `pg_stat_user_indexes` for zero-scan indexes on lab tables.
5. Write a query that seq-scans intentionally (`SELECT * FROM deployments WHERE version LIKE '%2.4%'`); discuss fix.
6. Drop test index if created: `DROP INDEX idx_deployments_status;`

**Stretch:** Insert 50k rows (section 7); compare plan times; use `CONCURRENTLY` in a note for prod.

---

## 9. DevOps connections

- **pg_stat_statements:** Extension capturing top queries by total time—install on RDS via parameter group.
- **ORM N+1:** App issues 1000 queries—fix in code, not only indexes.
- **Connection pooling:** Slow queries + too many connections = outage (Day 15).

---

## Quick reference

| Task | Command |
|------|---------|
| Plan | `EXPLAIN SELECT ...` |
| Run + plan | `EXPLAIN ANALYZE SELECT ...` |
| Create index | `CREATE INDEX idx ON t (col);` |
| Update stats | `ANALYZE table;` |
| Index usage | `pg_stat_user_indexes` |

**Next:** [Day 10 — Transactions, ACID & locking](../day10/)
