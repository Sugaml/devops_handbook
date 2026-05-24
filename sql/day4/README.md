# Day 4 — INSERT, UPDATE, DELETE & RETURNING

**Goal:** Modify data safely with DML, use `RETURNING` to capture generated rows, and practice rollback-friendly workflows before touching production.

**Time:** 3–4 hours

---

## 1. INSERT — add rows

```sql
INSERT INTO deployments (
    service_id, environment_id, version, status,
    deployed_by, started_at, finished_at
) VALUES (
    2, 1, '1.8.4', 'success',
    'ci-bot', now() - interval '1 hour', now() - interval '55 min'
);
```

Multiple rows:

```sql
INSERT INTO hosts (hostname, environment_id, ip_address, role, cpu_cores, mem_gb)
VALUES
    ('stg-worker-01', 1, '10.0.1.40', 'worker', 2, 8),
    ('stg-worker-02', 1, '10.0.1.41', 'worker', 2, 8);
```

### RETURNING (PostgreSQL)

```sql
INSERT INTO incidents (
    service_id, environment_id, severity, title, opened_at
) VALUES (
    3, 2, 'sev3', 'Batch queue backlog', now()
)
RETURNING id, title, opened_at;
```

Use in scripts to chain on new primary keys without a second query.

---

## 2. UPDATE — change existing rows

```sql
UPDATE deployments
SET status = 'success',
    finished_at = now()
WHERE id = (
    SELECT id FROM deployments
    WHERE status = 'running'
    ORDER BY started_at DESC
    LIMIT 1
);
```

**Always** constrain with `WHERE` unless you intend to touch every row.

```sql
UPDATE incidents
SET resolved_at = now()
WHERE id = 4 AND resolved_at IS NULL
RETURNING id, title, resolved_at;
```

---

## 3. DELETE — remove rows

```sql
DELETE FROM hosts
WHERE hostname = 'stg-worker-02';
```

Prefer soft deletes in production (`deleted_at` column)—hard delete only for GDPR/retention jobs.

---

## 4. Safe lab workflow: transactions

Wrap experiments so you can undo:

```sql
BEGIN;

INSERT INTO deployments (service_id, environment_id, version, status, deployed_by, started_at)
VALUES (1, 1, '9.9.9-test', 'pending', 'lab-you', now());

SELECT * FROM deployments WHERE version = '9.9.9-test';

ROLLBACK;   -- undoes the insert
-- COMMIT;  -- makes it permanent
```

Day 10 goes deeper on ACID and isolation.

---

## 5. Upsert with ON CONFLICT (PostgreSQL)

```sql
INSERT INTO services (name, team, criticality)
VALUES ('notifications', 'platform', 'medium')
ON CONFLICT (name) DO UPDATE
SET team = EXCLUDED.team,
    criticality = EXCLUDED.criticality;
```

Common for idempotent deploy metadata sync from CI.

---

## 6. DevOps-shaped DML examples

**Record a deployment start from CI:**

```sql
INSERT INTO deployments (
    service_id, environment_id, version, status,
    deployed_by, started_at
) VALUES (
    (SELECT id FROM services WHERE name = 'payments-api'),
    (SELECT id FROM environments WHERE name = 'staging'),
    '2.5.0-rc1', 'running', 'github-actions', now()
)
RETURNING id, version, started_at;
```

**Mark deploy failed:**

```sql
UPDATE deployments
SET status = 'failed', finished_at = now()
WHERE id = 42 AND status = 'running';
```

---

## 7. Pitfalls

| Mistake | Consequence |
|---------|-------------|
| Missing `WHERE` on UPDATE/DELETE | Full table change |
| Wrong `environment_id` | Data in wrong region |
| No transaction in scripts | Partial failure state |
| Storing secrets in rows | Credential leak in backups |

---

## 8. Lab — Day 4

From `sql/day4/labs/`:

1. `BEGIN`; run `insert_deployment.sql`; verify with SELECT; `ROLLBACK`.
2. Insert a new incident for `batch-worker` in staging (env id 1); use `RETURNING`.
3. Update the running deployment (`status = 'running'`) to `success` with `finished_at = now()`.
4. Insert two lab hosts; delete one by hostname; confirm count.
5. Practice upsert: insert `services` row `cache-service` twice with `ON CONFLICT` updating team.
6. Document how many rows each UPDATE affected (`GET DIAGNOSTICS` or check `RETURNING`).

**Stretch:** Write a single statement that inserts a deployment only if no row exists for same service+env+version (`ON CONFLICT` requires a unique constraint—add one in Day 5 lab).

---

## 9. DevOps connections

- **CI pipelines:** Insert deploy row at start; update at end—correlates with logs by `deployment.id`.
- **Idempotency:** `ON CONFLICT` prevents duplicate webhook processing.
- **Audit:** Prefer append-only event tables over silent UPDATE when compliance requires history.

---

## Quick reference

| Task | SQL |
|------|-----|
| Insert | `INSERT INTO t (cols) VALUES (...);` |
| Update | `UPDATE t SET col = v WHERE ...;` |
| Delete | `DELETE FROM t WHERE ...;` |
| Get new id | `INSERT ... RETURNING id;` |
| Undo lab | `BEGIN; ... ROLLBACK;` |

**Next:** [Day 5 — DDL & constraints](../day5/)
