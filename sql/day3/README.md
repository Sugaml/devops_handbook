# Day 3 — Sorting, Pagination & Data Types

**Goal:** Control result order with `ORDER BY`, paginate with `LIMIT`/`OFFSET`, understand PostgreSQL types and casting, and work confidently with timestamps in UTC.

**Time:** 3–4 hours

---

## 1. ORDER BY

```sql
SELECT hostname, cpu_cores, mem_gb
FROM hosts
ORDER BY mem_gb DESC, hostname ASC;
```

| Keyword | Meaning |
|---------|---------|
| `ASC` | Ascending (default) |
| `DESC` | Descending |
| `NULLS FIRST` / `NULLS LAST` | NULL placement (PostgreSQL) |

**Deployments newest first:**

```sql
SELECT version, status, started_at, finished_at
FROM deployments
ORDER BY started_at DESC;
```

Sort by expression:

```sql
SELECT hostname,
       mem_gb::float / cpu_cores AS gb_per_core
FROM hosts
ORDER BY gb_per_core DESC;
```

---

## 2. LIMIT and OFFSET (pagination)

```sql
-- Page 1: first 5 rows
SELECT version, status, started_at
FROM deployments
ORDER BY started_at DESC
LIMIT 5;

-- Page 2: next 5
SELECT version, status, started_at
FROM deployments
ORDER BY started_at DESC
LIMIT 5 OFFSET 5;
```

**Production note:** Deep `OFFSET` (e.g. 100000) scans and discards rows—use keyset pagination (`WHERE id < $last_id ORDER BY id DESC LIMIT 5`) for large tables.

---

## 3. DISTINCT — unique values

```sql
SELECT DISTINCT status FROM deployments;

SELECT DISTINCT role FROM hosts ORDER BY role;

-- DISTINCT ON (PostgreSQL): first row per group
SELECT DISTINCT ON (service_id)
    service_id, version, status, started_at
FROM deployments
ORDER BY service_id, started_at DESC;
```

`DISTINCT ON` requires `ORDER BY` starting with the same expressions—handy for "latest deploy per service."

---

## 4. Core PostgreSQL types (ops-relevant)

| Type | Use | Example |
|------|-----|---------|
| `TEXT` / `VARCHAR(n)` | Names, versions | `'2.4.1'` |
| `SMALLINT`, `INT`, `BIGINT` | IDs, counts | `8080` |
| `NUMERIC(p,s)` | Money, precise metrics | `99.99` |
| `BOOLEAN` | Flags | `TRUE` |
| `TIMESTAMPTZ` | Event times (always prefer) | `now()` |
| `DATE` | Day granularity | `'2024-05-01'` |
| `INET` | IP addresses | `'10.0.1.10'` |
| `JSONB` | Flexible metadata | `'{"region":"us-east-1"}'` |

Lab schema uses `TIMESTAMPTZ` for deploy and incident times—stored in UTC internally.

---

## 5. Casting and COALESCE

```sql
SELECT
    hostname,
    cpu_cores::text || ' cores' AS cpu_label,
    COALESCE(finished_at, started_at) AS last_activity
FROM deployments d
JOIN hosts h ON FALSE  -- placeholder; deployments have no host FK in lab
LIMIT 0;
```

Explicit cast forms:

```sql
SELECT CAST('8080' AS INT);
SELECT '8080'::INT;
```

`COALESCE(a, b, c)` returns first non-NULL argument—essential for dashboards.

---

## 6. Date and time arithmetic

```sql
SELECT
    version,
    started_at,
    finished_at,
    finished_at - started_at AS deploy_duration
FROM deployments
WHERE finished_at IS NOT NULL
ORDER BY deploy_duration DESC;

-- Filter last 48 hours
SELECT * FROM incidents
WHERE opened_at >= now() - interval '48 hours';

-- Truncate to day for grouping (preview Day 7)
SELECT date_trunc('day', started_at) AS deploy_day, count(*)
FROM deployments
GROUP BY 1;
```

Always document timezone in runbooks: **store UTC, display local in UI**.

---

## 7. String functions for logs and hostnames

```sql
SELECT
    upper(hostname),
    lower(role),
    length(hostname),
    split_part(hostname, '-', 1) AS prefix
FROM hosts
LIMIT 5;
```

---

## 8. Lab — Day 3

From `sql/day3/labs/`:

1. Run `sort_and_page.sql`; fetch page 2 of deployments (OFFSET 5).
2. List hosts sorted by `cpu_cores` DESC, then `hostname` ASC.
3. Use `DISTINCT` to list all deployment statuses ever recorded.
4. Compute deploy duration for successful deployments; sort longest first.
5. Write a query: incidents opened in the last 14 days, newest first.
6. Use `DISTINCT ON (service_id)` to get the latest deployment row per service.

**Stretch:** Add `NULLS LAST` when sorting by `finished_at DESC`.

---

## 9. DevOps connections

- **API pagination:** Same `LIMIT`/`OFFSET` (or cursor) patterns back REST list endpoints.
- **SLO windows:** `interval '30 days'` defines error-budget reporting periods.
- **Type mismatches:** Comparing `text` port to `int` fails—cast explicitly in migrations and scripts.

---

## Quick reference

| Task | SQL |
|------|-----|
| Sort | `ORDER BY col DESC` |
| Top N | `LIMIT N` |
| Page | `LIMIT N OFFSET M` |
| Unique | `SELECT DISTINCT col` |
| Cast | `col::type` |
| Default NULL | `COALESCE(col, 0)` |
| Duration | `end_ts - start_ts` |

**Next:** [Day 4 — INSERT, UPDATE, DELETE](../day4/)
