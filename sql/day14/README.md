# Day 14 — Schema Migrations in CI/CD

**Goal:** Version database schema in git, apply migrations with Flyway or Liquibase in pipelines, handle roll-forward vs rollback, and integrate SQL linting into pull requests.

**Time:** 4–5 hours

---

## 1. Why migrations beat manual DDL

| Manual `psql` | Migration tool |
|---------------|----------------|
| No audit trail | Versioned files in git |
| Drift between envs | Same order everywhere |
| Hero-dependent | CI applies on merge |

Tools track applied versions in a table (`flyway_schema_history`).

---

## 2. Flyway layout

```
sql/day14/labs/flyway/
├── conf/flyway.conf
└── sql/
    ├── V1__baseline.sql
    ├── V2__deployment_steps.sql
    └── V3__deployments_metadata.sql
```

Naming: `V{version}__{description}.sql` — immutable once applied to shared envs.

**Never edit** applied migrations; add `V4__fix_...` instead.

---

## 3. Flyway commands

```bash
cd sql/day14/labs/flyway

# JDBC URL to lab DB on host port 5433
export FLYWAY_URL=jdbc:postgresql://localhost:5433/handbook
export FLYWAY_USER=handbook
export FLYWAY_PASSWORD=handbook

flyway info
flyway migrate
flyway validate
```

Docker without local Flyway install:

```bash
docker run --rm -v "$PWD/sql:/flyway/sql" flyway/flyway \
  -url=jdbc:postgresql://host.docker.internal:5433/handbook \
  -user=handbook -password=handbook info
```

---

## 4. Baseline existing database

If DB existed before Flyway:

```bash
flyway baseline -baselineVersion=1 -baselineDescription=handbook_seed
```

Or `V1__baseline.sql` captures current schema snapshot for greenfield.

---

## 5. Safe migration patterns

**Expand-contract** for zero downtime:

1. V4: Add nullable column `deployments.canary_pct`
2. Deploy app reading/writing new column
3. V5: Backfill default, add NOT NULL
4. V6: Drop old column (if replacing)

**Avoid:**

- Long `ACCESS EXCLUSIVE` locks from careless `ALTER`
- Blocking `ADD COLUMN DEFAULT` on huge tables (Postgres 11+ optimized but still plan)

Use `CREATE INDEX CONCURRENTLY` in separate migration with `flyway:postgresql:transactional=false` or run outside Flyway transaction.

---

## 6. Rollback strategy

Flyway **Community** has no automatic down migrations—plan **roll-forward**:

- `V5__rollback_canary.sql` disables feature instead of `DOWN`
- Keep **restore from backup** for catastrophic failure (Day 13)

Liquibase supports `rollback` blocks; teams choose based on audit needs.

---

## 7. CI pipeline sketch (GitHub Actions)

```yaml
jobs:
  db-migrate:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: handbook
          POSTGRES_PASSWORD: handbook
          POSTGRES_DB: handbook_ci
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - name: Flyway migrate
        run: |
          docker run --rm --network host \
            -v ${{ github.workspace }}/sql/day14/labs/flyway/sql:/flyway/sql \
            flyway/flyway \
            -url=jdbc:postgresql://localhost:5432/handbook_ci \
            -user=handbook -password=handbook migrate
      - name: SQL lint
        run: pip install sqlfluff && sqlfluff lint sql/day14/labs/flyway/sql/
```

Run on every PR against ephemeral DB.

---

## 8. sqlfluff (style gate)

```bash
pip install sqlfluff sqlfluff-templater-dbt
sqlfluff lint sql/day14/labs/flyway/sql/V2__deployment_steps.sql --dialect postgres
```

Catches inconsistent casing, missing commas, dangerous patterns.

---

## 9. Lab — Day 14

1. Install Flyway CLI or use Docker image.
2. Apply migrations in `sql/day14/labs/flyway/sql/` to a **fresh** database `handbook_flyway` (create empty DB first).
3. Run `flyway info` — verify checksums.
4. Intentionally change an applied file; run `flyway validate` — observe failure.
5. Add `V4__add_service_owner.sql` with `ALTER TABLE services ADD COLUMN owner TEXT;`
6. Write 3-step expand-contract plan for renaming column `deployed_by` → `triggered_by`.

**Stretch:** Wire Flyway into a local GitHub Actions `act` run or document Jenkins stage.

---

## 10. DevOps connections

- **App + DB deploy order:** Backward-compatible migration **before** app rollout (expand); contract after all instances updated.
- **Terraform + Flyway:** Terraform provisions RDS; Flyway owns schema—clear ownership boundary.
- **Review:** DB migrations require DBA/ senior review like infra changes.

---

## Quick reference

| Task | Command |
|------|---------|
| Status | `flyway info` |
| Apply | `flyway migrate` |
| Check | `flyway validate` |
| Baseline | `flyway baseline` |
| Lint | `sqlfluff lint --dialect postgres` |

**Next:** [Day 15 — Production operations & runbooks](../day15/)
