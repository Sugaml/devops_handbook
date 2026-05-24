# Day 6 — JOINs: Combining Tables

**Goal:** Combine related tables with `INNER JOIN`, `LEFT JOIN`, and understand when rows appear or disappear—essential for inventory, deploy, and incident reports.

**Time:** 4 hours

---

## 1. Why JOINs?

Data is normalized across tables. A deployment row stores `service_id`, not the service name—you JOIN to `services` for human-readable output.

```
deployments.service_id  ──►  services.id
deployments.environment_id  ──►  environments.id
```

---

## 2. INNER JOIN — matching rows only

```sql
SELECT
    d.version,
    d.status,
    s.name AS service_name,
    e.name AS environment_name
FROM deployments AS d
INNER JOIN services AS s ON s.id = d.service_id
INNER JOIN environments AS e ON e.id = d.environment_id
ORDER BY d.started_at DESC;
```

Only deployments with valid FK references appear. Orphan ids (if constraints disabled) drop out.

---

## 3. LEFT JOIN — keep left table rows

```sql
SELECT
    s.name AS service_name,
    d.version,
    d.started_at
FROM services AS s
LEFT JOIN deployments AS d ON d.service_id = s.id
ORDER BY s.name, d.started_at DESC NULLS LAST;
```

Services **never deployed** still appear with NULL deploy columns—useful for coverage audits.

---

## 4. JOIN diagram (mental model)

```
INNER JOIN     LEFT JOIN
  A ∩ B          all A + matching B
```

| Join type | When to use |
|-----------|-------------|
| `INNER JOIN` | Only matched pairs |
| `LEFT JOIN` | All from left + optional right |
| `RIGHT JOIN` | Rare; rewrite as LEFT JOIN |
| `FULL OUTER JOIN` | Unmatched from both sides |
| `CROSS JOIN` | Cartesian product (generators, tests) |

---

## 5. Joining three+ tables

**Hosts with environment region:**

```sql
SELECT
    h.hostname,
    h.role,
    e.name AS env,
    e.region
FROM hosts AS h
JOIN environments AS e ON e.id = h.environment_id
WHERE e.tier = 'prod';
```

**Incidents with service and environment:**

```sql
SELECT
    i.title,
    i.severity,
    s.name AS service,
    e.name AS environment,
    i.opened_at
FROM incidents AS i
JOIN services AS s ON s.id = i.service_id
JOIN environments AS e ON e.id = i.environment_id
WHERE i.resolved_at IS NULL;
```

---

## 6. Join conditions vs filter conditions

```sql
-- Filter in WHERE (usually clearer for optional LEFT JOIN)
FROM services s
LEFT JOIN deployments d ON d.service_id = s.id AND d.environment_id = 2

-- vs moving env filter to WHERE (turns LEFT into INNER effectively)
LEFT JOIN deployments d ON d.service_id = s.id
WHERE d.environment_id = 2 OR d.id IS NULL
```

Put optional match criteria in `ON` for LEFT JOINs; reserve `WHERE` for row filters after join.

---

## 7. Self-joins (same table twice)

Compare consecutive deploys per service—advanced preview; pattern:

```sql
SELECT a.version AS from_version, b.version AS to_version
FROM deployments a
JOIN deployments b ON a.service_id = b.service_id
  AND b.started_at > a.started_at;
```

---

## 8. Anti-join pattern (services without prod deploys)

```sql
SELECT s.name
FROM services s
LEFT JOIN deployments d
    ON d.service_id = s.id
   AND d.environment_id = (SELECT id FROM environments WHERE name = 'production' AND region = 'us-east-1')
WHERE d.id IS NULL;
```

Day 8 covers `NOT EXISTS`—often clearer.

---

## 9. Lab — Day 6

From `sql/day6/labs/`:

1. Run `join_deployments.sql`; add column `deployed_by`.
2. List every host with environment name and region (INNER JOIN).
3. LEFT JOIN all services to deployments; count services with zero deploys.
4. Show open incidents with service name, environment name, severity.
5. Find failed/rolled_back deploys with service and environment labels.
6. Explain difference between `JOIN` and `INNER JOIN` (none in PostgreSQL).

**Stretch:** Join `deployment_steps` (Day 5) to deployments and list step names for one deploy.

---

## 10. DevOps connections

- **Grafana SQL panels:** Almost always multi-table JOINs—prototype in `psql`.
- **Inventory drift:** LEFT JOIN expected hosts vs live CMDB export.
- **Blast radius:** JOIN incident → service → latest deployment version.

---

## Quick reference

| Task | Pattern |
|------|---------|
| Inner join | `FROM a JOIN b ON a.id = b.a_id` |
| Left join | `FROM a LEFT JOIN b ON ...` |
| Multiple | Chain `JOIN` clauses |
| Alias | `FROM deployments d` |

**Next:** [Day 7 — Aggregations & window functions](../day7/)
