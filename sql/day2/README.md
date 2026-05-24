# Day 2 — Filtering with WHERE, Operators & NULL

**Goal:** Narrow result sets with `WHERE`, combine conditions with `AND`/`OR`, handle `NULL` correctly, and use `IN`, `BETWEEN`, and pattern matching for ops queries.

**Time:** 3–4 hours

---

## 1. The WHERE clause

```sql
SELECT hostname, ip_address, role
FROM hosts
WHERE environment_id = 2;
```

Without `WHERE`, you scan every row. On small lab data that is instant; on production tables with millions of rows, filters and indexes (Day 9) matter.

---

## 2. Comparison operators

| Operator | Meaning |
|----------|---------|
| `=`, `<>` or `!=` | Equal / not equal |
| `<`, `<=`, `>`, `>=` | Ordering |
| `BETWEEN a AND b` | Inclusive range |
| `IN (v1, v2, ...)` | Match any listed value |
| `LIKE pattern` | Text pattern (`%`, `_`) |
| `ILIKE` | Case-insensitive LIKE (PostgreSQL) |

```sql
-- Deployments that failed or were rolled back
SELECT version, status, started_at
FROM deployments
WHERE status IN ('failed', 'rolled_back');

-- Hosts with at least 8 GB RAM
SELECT hostname, mem_gb
FROM hosts
WHERE mem_gb >= 8;

-- Incidents in the last 7 days
SELECT title, severity, opened_at
FROM incidents
WHERE opened_at >= now() - interval '7 days';
```

---

## 3. AND, OR, and parentheses

```sql
SELECT hostname, role, cpu_cores
FROM hosts
WHERE environment_id = 2
  AND role IN ('api', 'web')
  AND cpu_cores >= 4;

-- Use parentheses to avoid logic bugs
SELECT *
FROM deployments
WHERE (status = 'failed' OR status = 'rolled_back')
  AND environment_id = 2;
```

**Pitfall:** `AND` binds tighter than `OR`. Always parenthesize mixed logic.

---

## 4. NULL — the silent bug

`NULL` means **unknown**, not zero or empty string.

```sql
-- WRONG: returns no rows if finished_at is NULL
SELECT * FROM deployments WHERE finished_at = NULL;

-- RIGHT
SELECT * FROM deployments WHERE finished_at IS NULL;

SELECT * FROM deployments WHERE finished_at IS NOT NULL;
```

| Expression | Result |
|------------|--------|
| `NULL = NULL` | Unknown (not TRUE) |
| `NULL AND TRUE` | NULL |
| `NULL OR FALSE` | NULL |

**Running deployments** (not finished yet):

```sql
SELECT service_id, version, status, started_at
FROM deployments
WHERE finished_at IS NULL
  AND status = 'running';
```

---

## 5. NOT IN trap with NULL

```sql
-- If any subquery row is NULL, NOT IN may return zero rows unexpectedly
SELECT name FROM services
WHERE id NOT IN (SELECT service_id FROM incidents WHERE resolved_at IS NULL OR TRUE);
```

Prefer `NOT EXISTS` (Day 8) for safety. For simple lists, `NOT IN` is fine when values are non-null.

---

## 6. Pattern matching with LIKE

| Pattern | Matches |
|---------|---------|
| `'prod-%'` | Starts with `prod-` |
| `'%api%'` | Contains `api` |
| `'prod-web-_'` | `prod-web-` + exactly one char |

```sql
SELECT hostname FROM hosts WHERE hostname LIKE 'prod-%';
SELECT hostname FROM hosts WHERE hostname ILIKE 'PROD-%';  -- case-insensitive
```

For regex, PostgreSQL offers `~` and `~*`:

```sql
SELECT hostname FROM hosts WHERE hostname ~ '^prod-api-[0-9]+$';
```

---

## 7. Boolean columns

```sql
-- If you add is_active boolean later:
-- WHERE is_active = TRUE
-- Shorthand (idiomatic):
-- WHERE is_active
```

---

## 8. Practical ops filters

**Open incidents (unresolved):**

```sql
SELECT i.title, i.severity, s.name AS service
FROM incidents i
JOIN services s ON s.id = i.service_id
WHERE i.resolved_at IS NULL
ORDER BY i.opened_at DESC;
```

**High-criticality services with a sev1/sev2 in production:**

```sql
SELECT DISTINCT s.name, s.criticality, i.severity
FROM services s
JOIN incidents i ON i.service_id = s.id
WHERE s.criticality = 'high'
  AND i.severity IN ('sev1', 'sev2')
  AND i.environment_id = 2;
```

---

## 9. Lab — Day 2

From `sql/day2/labs/`:

1. Run `filter_deployments.sql`; change status list to only `'success'`.
2. Find all hosts in environment id `1` with `role = 'web'`.
3. List incidents where `severity = 'sev1'` OR (`severity = 'sev2'` AND `environment_id = 2`).
4. Write a query for deployments where `finished_at IS NULL`.
5. Find hostnames matching `%-api-%` using `LIKE`.
6. Explain why `WHERE resolved_at = NULL` fails—run it and compare to `IS NULL`.

**Stretch:** Add a `WHERE` using `BETWEEN` on `started_at` for deployments in the last 72 hours.

---

## 10. DevOps connections

- **Alert queries:** Grafana PostgreSQL datasource uses the same `WHERE` patterns—test in `psql` first.
- **Log correlation:** Filter by time range + service id—the bread and butter of incident SQL.
- **NULL in metrics:** Missing data ≠ zero; dashboards must use `COALESCE` or separate "no data" handling (Day 3).

---

## Quick reference

| Task | SQL |
|------|-----|
| Equality | `WHERE col = 'value'` |
| NULL check | `WHERE col IS NULL` |
| List | `WHERE col IN ('a','b')` |
| Range | `WHERE n BETWEEN 1 AND 10` |
| Pattern | `WHERE col LIKE 'prod-%'` |
| Recent | `WHERE ts >= now() - interval '1 day'` |

**Next:** [Day 3 — Sorting, pagination & data types](../day3/)
