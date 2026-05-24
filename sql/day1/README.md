# Day 1 — RDBMS Basics, PostgreSQL Setup & First Queries

**Goal:** Understand why relational databases matter in DevOps, run PostgreSQL locally with Docker, connect with `psql`, and write your first `SELECT` statements against real ops-shaped data.

**Time:** 3–4 hours

---

## 1. Why SQL for DevOps?

| Use case | SQL role |
|----------|----------|
| Incident triage | Join deploy history with error spikes |
| Inventory | Hosts, regions, versions across environments |
| CI/CD metadata | Deployment status, rollback audit trail |
| Observability | Query metrics/logs stored in SQL (Grafana, custom) |
| Runbooks | Reusable queries for on-call (read-only role) |

You will not replace Prometheus with SQL—but **every platform team** touches a database for app state, config, or reporting.

---

## 2. Relational model in 60 seconds

```
environments ──┬── hosts
               │
services ──────┼── deployments
               │
               └── incidents
```

- **Table** = entity (e.g. `hosts`)
- **Row** = one record (one server)
- **Column** = attribute (`hostname`, `cpu_cores`)
- **Primary key (PK)** = unique row identifier
- **Foreign key (FK)** = link to another table's PK

SQL is **declarative**: you describe *what* you want; the engine decides *how* to fetch it.

---

## 3. Start the lab database

From the `sql/` directory:

```bash
docker compose up -d
docker compose logs db | tail -5
docker compose exec db psql -U handbook -d handbook
```

Connection string for GUI clients (DBeaver, pgAdmin, DataGrip):

```
postgresql://handbook:handbook@localhost:5433/handbook
```

Verify tables loaded:

```sql
\dt
\d hosts
```

---

## 4. `psql` essentials

| Command | Purpose |
|---------|---------|
| `\?` | Help |
| `\dt` | List tables |
| `\d table` | Describe table |
| `\x` | Toggle expanded output (wide rows) |
| `\timing` | Show query duration |
| `\q` | Quit |

Run a file:

```bash
docker compose exec db psql -U handbook -d handbook -f /path/on/host/day1/labs/basic_select.sql
```

From inside `psql`:

```sql
\i labs/day1/labs/basic_select.sql   -- path relative to where you launched psql
```

---

## 5. Anatomy of a SELECT

```sql
SELECT column1, column2          -- which columns (or expressions)
FROM   table_name                 -- source table
-- WHERE  condition               -- filter (Day 2)
-- ORDER BY column                -- sort (Day 3)
-- LIMIT n;                       -- cap rows (Day 3)
```

### Select all columns (sparingly in production)

```sql
SELECT * FROM environments;
```

Prefer naming columns—schema changes won't break scripts silently.

### Select specific columns

```sql
SELECT name, region, tier
FROM environments;
```

### Column aliases

```sql
SELECT
    hostname AS host,
    cpu_cores AS cpus,
    mem_gb AS memory_gb
FROM hosts;
```

Aliases appear in result headers; use them for reports and CSV exports.

---

## 6. Literals and expressions

```sql
SELECT
    hostname,
    cpu_cores * 2 AS hypothetical_cpus,
    mem_gb || ' GB' AS memory_label    -- string concat with ||
FROM hosts
LIMIT 3;
```

| Type | Example |
|------|---------|
| Text | `'staging'`, `'us-east-1'` |
| Integer | `4`, `8080` |
| Boolean | `TRUE`, `FALSE` |
| Timestamp | `'2024-01-15 10:00:00+00'` |
| NULL | missing value (Day 2) |

---

## 7. First ops queries

**All production hosts:**

```sql
SELECT hostname, ip_address, role
FROM hosts h
JOIN environments e ON e.id = h.environment_id
WHERE e.tier = 'prod';
```

Preview of JOINs—you will master them on Day 6. For today, simpler filters work too:

```sql
SELECT hostname, role, cpu_cores
FROM hosts
WHERE environment_id = 2;
```

**Recent deployments (preview):**

```sql
SELECT version, status, deployed_by, started_at
FROM deployments
ORDER BY started_at DESC
LIMIT 5;
```

---

## 8. SQL style for teams

```sql
-- Good: keywords UPPER, identifiers lower, one clause per line
SELECT
    d.version,
    d.status,
    s.name AS service_name
FROM deployments AS d
JOIN services AS s ON s.id = d.service_id;
```

- End statements with `;`
- Use meaningful table aliases (`d`, `s`, not `t1`, `t2`)
- Avoid `SELECT *` in automation—pin columns

---

## 9. Lab — Day 1

Work from `sql/day1/labs/`. Ensure Docker Compose is running.

1. Connect with `psql`; run `\dt` and `\d deployments`.
2. Run `labs/basic_select.sql` line by line; note row counts.
3. Write a query listing every service `name` and `team`.
4. List hostnames and `mem_gb` where `role = 'api'`.
5. Select `version`, `status`, `started_at` from deployments; sort newest first; limit 3.
6. Turn on `\timing` and re-run the deployment query—note milliseconds (baseline for Day 9).

**Stretch:** Install [DBeaver](https://dbeaver.io/) or use VS Code SQLTools; save the connection and export query results to CSV.

---

## 10. DevOps connections

- **12-factor apps:** Config in env vars; persistent state in PostgreSQL/MySQL/Redis.
- **Secrets:** Never embed passwords in SQL files—use env vars or secret managers (Day 12).
- **Read-only on-call:** Give responders SELECT-only access to prod replicas.

---

## Quick reference

| Task | Command |
|------|---------|
| Start DB | `docker compose up -d` (from `sql/`) |
| Connect | `docker compose exec db psql -U handbook -d handbook` |
| List tables | `\dt` |
| Describe | `\d hosts` |
| Basic query | `SELECT col FROM tbl;` |

**Next:** [Day 2 — Filtering & NULL](../day2/)
