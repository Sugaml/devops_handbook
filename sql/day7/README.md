# Day 7 — Aggregations, GROUP BY, HAVING & Windows

**Goal:** Summarize fleet and deploy data with aggregate functions, filter groups with `HAVING`, and introduce window functions for rankings and running totals.

**Time:** 4 hours

---

## 1. Aggregate functions

| Function | Purpose |
|----------|---------|
| `COUNT(*)` | Row count |
| `COUNT(col)` | Non-NULL values in column |
| `SUM(col)` | Total |
| `AVG(col)` | Mean |
| `MIN`, `MAX` | Extremes |

```sql
SELECT
    COUNT(*) AS total_hosts,
    SUM(cpu_cores) AS total_cores,
    AVG(mem_gb)::numeric(10,1) AS avg_mem_gb
FROM hosts;
```

---

## 2. GROUP BY

```sql
SELECT
    e.name AS environment,
    COUNT(*) AS host_count,
    SUM(h.cpu_cores) AS total_cpus
FROM hosts h
JOIN environments e ON e.id = h.environment_id
GROUP BY e.id, e.name
ORDER BY host_count DESC;
```

Every non-aggregated SELECT column must appear in `GROUP BY` (or be functionally dependent on PK in PostgreSQL).

---

## 3. HAVING — filter groups

`WHERE` filters rows **before** grouping; `HAVING` filters **after**.

```sql
SELECT
    s.name AS service,
    COUNT(*) FILTER (WHERE d.status = 'failed') AS failed_deploys
FROM services s
JOIN deployments d ON d.service_id = s.id
GROUP BY s.id, s.name
HAVING COUNT(*) FILTER (WHERE d.status = 'failed') > 0;
```

`FILTER` clause (PostgreSQL) is cleaner than `SUM(CASE WHEN ...)`.

---

## 4. Deployments per day

```sql
SELECT
    date_trunc('day', started_at AT TIME ZONE 'UTC') AS deploy_day,
    COUNT(*) AS deploys,
    COUNT(*) FILTER (WHERE status = 'success') AS successes
FROM deployments
GROUP BY 1
ORDER BY 1 DESC;
```

---

## 5. COUNT pitfalls

```sql
SELECT COUNT(*) FROM deployments;           -- all rows
SELECT COUNT(finished_at) FROM deployments; -- excludes NULL finished_at
SELECT COUNT(DISTINCT service_id) FROM deployments;
```

---

## 6. Window functions (intro)

Aggregates collapse rows; windows keep detail rows and add computed columns.

```sql
SELECT
    service_id,
    version,
    status,
    started_at,
    ROW_NUMBER() OVER (
        PARTITION BY service_id
        ORDER BY started_at DESC
    ) AS deploy_rank
FROM deployments;
```

`deploy_rank = 1` → latest deploy per service.

**Latest deploy per service (alternative to DISTINCT ON):**

```sql
SELECT * FROM (
    SELECT
        d.*,
        ROW_NUMBER() OVER (
            PARTITION BY service_id ORDER BY started_at DESC
        ) AS rn
    FROM deployments d
) t
WHERE rn = 1;
```

Other windows: `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`, `SUM() OVER (...)`.

---

## 7. Rolling deploy success rate (7-day)

```sql
SELECT
    date_trunc('day', started_at) AS day,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0),
        1
    ) AS success_pct
FROM deployments
WHERE started_at >= now() - interval '7 days'
GROUP BY 1
ORDER BY 1;
```

`NULLIF` avoids divide-by-zero.

---

## 8. Lab — Day 7

From `sql/day7/labs/`:

1. Run `aggregations.sql`; interpret each result set.
2. Host count and total memory per `role`.
3. Deploy count by `status`; only groups with count ≥ 1 (trivial) then filter failed > 0 with HAVING.
4. Average deploy duration (`finished_at - started_at`) for successful deploys.
5. Use `ROW_NUMBER()` to list top 2 newest deploys per service.
6. Open incident count by `severity`.

**Stretch:** `LAG(version)` to compare current deploy version to previous per service.

---

## 9. DevOps connections

- **SLO dashboards:** Daily error rates = grouped aggregates over time buckets.
- **Capacity:** `SUM(cpu_cores)` by environment feeds planning spreadsheets.
- **Change failure rate:** Failed deploys / total deploys (DORA metric).

---

## Quick reference

| Task | SQL |
|------|-----|
| Group count | `GROUP BY col` + `COUNT(*)` |
| Filter groups | `HAVING count(*) > n` |
| Conditional agg | `COUNT(*) FILTER (WHERE ...)` |
| Rank | `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` |
| Safe divide | `... / NULLIF(denom, 0)` |

**Next:** [Day 8 — Subqueries & CTEs](../day8/)
