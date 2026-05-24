# Day 8 — Subqueries, CTEs & EXISTS

**Goal:** Write readable multi-step queries with Common Table Expressions (CTEs), use subqueries in `FROM` and `WHERE`, and prefer `EXISTS` for semi-joins.

**Time:** 4 hours

---

## 1. Scalar subquery

Returns one value—used in SELECT or WHERE:

```sql
SELECT
    name,
    (SELECT COUNT(*) FROM hosts h WHERE h.environment_id = e.id) AS host_count
FROM environments e;
```

Must return exactly one row/column or you get a runtime error.

---

## 2. Subquery in FROM (derived table)

```sql
SELECT env_name, deploys
FROM (
    SELECT e.name AS env_name, COUNT(d.id) AS deploys
    FROM environments e
    LEFT JOIN deployments d ON d.environment_id = e.id
    GROUP BY e.id, e.name
) AS stats
WHERE deploys > 2;
```

Always alias derived tables.

---

## 3. CTEs — WITH clause

Same logic, often clearer:

```sql
WITH deploy_stats AS (
    SELECT
        environment_id,
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE status = 'failed') AS failed
    FROM deployments
    GROUP BY environment_id
)
SELECT e.name, ds.total, ds.failed
FROM environments e
JOIN deploy_stats ds ON ds.environment_id = e.id;
```

Chain multiple CTEs:

```sql
WITH recent AS (
    SELECT * FROM deployments
    WHERE started_at >= now() - interval '30 days'
),
failed AS (
    SELECT * FROM recent WHERE status IN ('failed', 'rolled_back')
)
SELECT s.name, COUNT(*) FROM failed f
JOIN services s ON s.id = f.service_id
GROUP BY s.name;
```

---

## 4. EXISTS vs IN

**Services that have ever failed in production:**

```sql
SELECT s.name
FROM services s
WHERE EXISTS (
    SELECT 1
    FROM deployments d
    JOIN environments e ON e.id = d.environment_id
    WHERE d.service_id = s.id
      AND d.status = 'failed'
      AND e.tier = 'prod'
);
```

`EXISTS` stops at first match—often faster than `IN (subquery)` on large sets.

**NOT EXISTS** for anti-join:

```sql
SELECT s.name
FROM services s
WHERE NOT EXISTS (
    SELECT 1 FROM deployments d WHERE d.service_id = s.id
);
```

---

## 5. CTE for incident + latest deploy correlation

```sql
WITH latest_deploy AS (
    SELECT DISTINCT ON (service_id, environment_id)
        service_id, environment_id, version, started_at
    FROM deployments
    ORDER BY service_id, environment_id, started_at DESC
)
SELECT
    i.title,
    i.severity,
    ld.version AS deploy_at_incident_time
FROM incidents i
LEFT JOIN latest_deploy ld
    ON ld.service_id = i.service_id
   AND ld.environment_id = i.environment_id
WHERE i.resolved_at IS NULL;
```

(Correlation is approximate—production would join on timestamp range.)

---

## 6. Readable runbook query structure

```sql
-- 1) params / filters as CTE
-- 2) core facts
-- 3) final SELECT for humans
WITH params AS (
    SELECT 'production'::text AS env_name, interval '7 days' AS window
),
target_env AS (
    SELECT id FROM environments, params
    WHERE environments.name = params.env_name
    LIMIT 1
)
SELECT d.version, d.status, d.started_at
FROM deployments d, target_env te
WHERE d.environment_id = te.id
  AND d.started_at >= now() - (SELECT window FROM params);
```

---

## 7. Lab — Day 8

From `sql/day8/labs/`:

1. Run `cte_incidents.sql`; modify window to 30 days.
2. Rewrite a Day 6 JOIN query using a CTE for the filtered deployment subset.
3. List environments with zero hosts using `NOT EXISTS`.
4. Use scalar subquery to show total incident count beside each service name.
5. Find services where failed deploy count > successful deploy count (CTE + HAVING).
6. Compare `IN (SELECT ...)` vs `EXISTS` for same result—check `\timing`.

**Stretch:** Recursive CTE to walk `deployment_steps` ordered by `step_order` (if table exists).

---

## 8. DevOps connections

- **Runbooks:** One saved CTE query per alert—parameters at top.
- **BI tools:** dbt models are stacked CTEs/materialized views.
- **Readability beats cleverness:** On-call at 3am reads top-to-bottom CTEs.

---

## Quick reference

| Task | Pattern |
|------|---------|
| CTE | `WITH name AS (SELECT ...) SELECT ...` |
| Exists | `WHERE EXISTS (SELECT 1 FROM ... WHERE ...)` |
| Scalar | `(SELECT count(*) FROM t WHERE ...)` |
| Derived | `FROM (SELECT ...) AS alias` |

**Next:** [Day 9 — Indexes & EXPLAIN](../day9/)
