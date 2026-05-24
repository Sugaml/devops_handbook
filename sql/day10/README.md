# Day 10 — Transactions, ACID, Isolation & Locking

**Goal:** Use transactions for atomic changes, understand ACID guarantees and isolation levels, avoid deadlocks, and write idempotent maintenance scripts.

**Time:** 4 hours

---

## 1. ACID recap

| Property | Meaning for ops |
|----------|-----------------|
| **Atomicity** | All statements commit or none (`BEGIN`/`COMMIT`/`ROLLBACK`) |
| **Consistency** | Constraints hold after commit |
| **Isolation** | Concurrent sessions don't corrupt each other |
| **Durability** | Committed data survives crash (WAL) |

---

## 2. Transaction syntax

```sql
BEGIN;   -- or START TRANSACTION;

UPDATE deployments SET status = 'success', finished_at = now()
WHERE id = 7 AND status = 'running';

INSERT INTO deployment_steps (deployment_id, step_name, step_order, status)
VALUES (7, 'smoke_test', 4, 'ok');

COMMIT;
-- ROLLBACK; if anything wrong
```

Savepoints for partial rollback:

```sql
BEGIN;
INSERT INTO hosts (...) VALUES (...);
SAVEPOINT after_host;
UPDATE deployments SET status = 'failed' WHERE id = 999;  -- oops
ROLLBACK TO SAVEPOINT after_host;
COMMIT;
```

---

## 3. Isolation levels (PostgreSQL)

```sql
SHOW transaction_isolation;  -- default: read committed
```

| Level | Behavior |
|-------|----------|
| Read committed | See committed rows only; each statement snapshot |
| Repeatable read | Same snapshot for whole transaction |
| Serializable | Strictest; may fail with serialization errors |

```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT COUNT(*) FROM deployments;
-- ... other session inserts ...
SELECT COUNT(*) FROM deployments;  -- same count
COMMIT;
```

Most apps use **Read committed**; financial/ledger systems may need Serializable.

---

## 4. Row-level locks

```sql
BEGIN;
SELECT * FROM deployments WHERE id = 3 FOR UPDATE;
-- row locked until COMMIT; other sessions block on conflicting UPDATE
UPDATE deployments SET status = 'success' WHERE id = 3;
COMMIT;
```

| Clause | Use |
|--------|-----|
| `FOR UPDATE` | Exclusive lock for update |
| `FOR SHARE` | Shared lock |
| `FOR UPDATE SKIP LOCKED` | Job queue workers skip busy rows |
| `NOWAIT` | Fail immediately if locked |

**Queue worker pattern:**

```sql
UPDATE deployments
SET status = 'running', deployed_by = 'worker-1'
WHERE id = (
    SELECT id FROM deployments
    WHERE status = 'pending'
    ORDER BY started_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING *;
```

---

## 5. Deadlocks

Session A locks row 1, wants row 2. Session B locks row 2, wants row 1. PostgreSQL detects and aborts one transaction.

**Prevention:** Lock rows in consistent order; keep transactions short.

---

## 6. Idempotent migration script pattern

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations (version)
VALUES ('20240524_add_deployment_steps')
ON CONFLICT DO NOTHING;

-- DDL here only if not already applied (Flyway does this for you)

COMMIT;
```

Day 14 covers Flyway/Liquibase formally.

---

## 7. DDL and transactions

PostgreSQL allows most DDL inside transactions—`CREATE TABLE` can `ROLLBACK`. Some ops ( `CREATE INDEX CONCURRENTLY`) cannot run in a transaction.

---

## 8. Lab — Day 10

From `sql/day10/labs/`:

1. Open two `psql` sessions. Session A: `BEGIN; SELECT * FROM deployments WHERE id = 1 FOR UPDATE;` Session B: try `UPDATE deployments SET status = 'pending' WHERE id = 1;` — observe block until A commits.
2. Run `transaction_deploy.sql` in a transaction; `ROLLBACK` and verify no change.
3. Simulate failed deploy: update status to `failed` and insert step row atomically.
4. Use `FOR UPDATE SKIP LOCKED` on two sessions competing for `pending` rows (insert test pending rows first).
5. Read PostgreSQL log for deadlock (optional—harder in Docker without config).

**Stretch:** Set `REPEATABLE READ` and demonstrate phantom vs non-phantom behavior with a second session.

---

## 9. DevOps connections

- **Blue/green deploy:** Transaction wraps config swap + health check flag.
- **Kubernetes job + DB:** Job must handle retry on serialization failure (`40001`).
- **Long transactions:** Block vacuum, bloat WAL—kill runaway sessions in incidents.

```sql
SELECT pid, state, query, now() - xact_start AS duration
FROM pg_stat_activity
WHERE state != 'idle' AND xact_start IS NOT NULL
ORDER BY duration DESC;
```

---

## Quick reference

| Task | SQL |
|------|-----|
| Start txn | `BEGIN;` |
| Commit | `COMMIT;` |
| Rollback | `ROLLBACK;` |
| Lock row | `SELECT ... FOR UPDATE` |
| Skip locked | `FOR UPDATE SKIP LOCKED` |
| Active txns | `pg_stat_activity` |

**Next:** [Day 11 — Schema design for DevOps](../day11/)
