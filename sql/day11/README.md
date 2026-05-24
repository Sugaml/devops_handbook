# Day 11 — Schema Design & Normalization for DevOps

**Goal:** Design maintainable schemas for platform data—normalization, naming conventions, audit columns, enums vs lookup tables, and JSONB for flexible metadata.

**Time:** 4–5 hours

---

## 1. Normalization (practical view)

| Normal form | Rule of thumb |
|-------------|---------------|
| 1NF | Atomic columns; no repeating groups |
| 2NF | No partial dependency on composite key |
| 3NF | No transitive dependency (city → zip → id) |

**Denormalize deliberately** for read-heavy dashboards—duplicate `service_name` on events if join cost matters and staleness is OK.

Handbook schema is **3NF**: environments, services, deployments separated.

---

## 2. Naming conventions

```sql
-- Tables: plural snake_case
-- deployments, deployment_steps

-- PK: id or table_id
-- FK: service_id references services(id)

-- Timestamps: created_at, updated_at, deleted_at (soft delete)
-- Booleans: is_active, not active_flag
```

Avoid reserved words (`user` → `app_users`).

---

## 3. Audit columns

```sql
ALTER TABLE deployments
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER deployments_updated_at
BEFORE UPDATE ON deployments
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

PostgreSQL 16+ uses `EXECUTE FUNCTION`; older versions: `EXECUTE PROCEDURE`.

---

## 4. ENUM vs lookup table vs CHECK

```sql
CREATE TYPE deploy_status AS ENUM (
    'pending', 'running', 'success', 'failed', 'rolled_back'
);
```

| Approach | Pros | Cons |
|----------|------|------|
| `CHECK (status IN (...))` | Simple migrations | No central type |
| `ENUM` | Compact, typed | Hard to rename values |
| Lookup table | Flexible, FK | Extra join |

For ops catalogs that change rarely, `CHECK` or lookup table is easiest in CI migrations.

---

## 5. JSONB for extensibility

```sql
ALTER TABLE deployments
ADD COLUMN metadata JSONB NOT NULL DEFAULT '{}';

UPDATE deployments
SET metadata = jsonb_build_object(
    'git_sha', 'a1b2c3d',
    'pipeline_url', 'https://ci.example/run/42'
)
WHERE id = 1;

SELECT version, metadata->>'git_sha' AS sha
FROM deployments
WHERE metadata ? 'git_sha';
```

Index JSON paths when queried often:

```sql
CREATE INDEX idx_deploy_metadata_git ON deployments ((metadata->>'git_sha'));
```

---

## 6. Multi-tenancy sketch

```sql
-- Every tenant-scoped table includes:
tenant_id UUID NOT NULL REFERENCES tenants(id)
-- Composite unique: UNIQUE (tenant_id, name)
-- Row Level Security (Day 12) enforces tenant_id = current_setting(...)
```

---

## 7. Time-series and metrics

High-volume metrics belong in **TimescaleDB**, Prometheus, or ClickHouse—not raw PostgreSQL rows without partitioning.

If you must store in Postgres:

```sql
CREATE TABLE metric_samples (
    time        TIMESTAMPTZ NOT NULL,
    service_id  SMALLINT NOT NULL,
    metric      TEXT NOT NULL,
    value       DOUBLE PRECISION NOT NULL
) PARTITION BY RANGE (time);
```

---

## 8. Lab — Day 11

From `sql/day11/labs/`:

1. Run `audit_and_metadata.sql` (review before commit).
2. Add `updated_at` trigger to `services`.
3. Insert deployment with JSONB metadata (`git_sha`, `build_id`); query by sha.
4. Design on paper (or SQL comments) a `runbooks` table: link to service, store markdown URL, tags.
5. Identify one denormalization you would add for a Grafana dashboard and justify it.
6. List three columns you would **never** store (passwords, raw credit cards, unbounded log blobs).

**Stretch:** Create `deploy_status` ENUM and migrate one column—note migration complexity.

---

## 9. DevOps connections

- **Event sourcing:** Append-only `deployment_events` instead of overwriting status.
- **Config vs inventory:** CMDB hosts vs live cloud API—schema should track `last_seen_at`.
- **Documentation:** Schema in git (dbdocs, Atlas HCL) reviewed like application code.

---

## Quick reference

| Decision | Recommendation |
|----------|----------------|
| Timestamps | `TIMESTAMPTZ`, UTC |
| Soft delete | `deleted_at` + partial unique indexes |
| Flexible attrs | JSONB + GIN index if searched |
| Status values | Lookup table or CHECK |
| Audit | `created_at`, `updated_at`, optional `created_by` |

**Next:** [Day 12 — Roles, grants & least privilege](../day12/)
