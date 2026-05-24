# SQL for DevOps — 15-Day Handbook

A practical path from your first `SELECT` to production database operations: schema design, performance, backups, migrations, and how SQL fits into CI/CD, observability, and incident response.

PostgreSQL is the primary engine (widely used on RDS, Cloud SQL, and self-hosted). Patterns transfer to MySQL/MariaDB with syntax differences called out where relevant.

## Structure — Days 1–15

| Day | Topic | Focus | Folder |
|-----|--------|-------|--------|
| 1 | RDBMS basics & setup | Why SQL for ops, Docker + `psql`, first queries | [day1](./day1/) |
| 2 | Filtering & NULL | `WHERE`, operators, `IS NULL`, `LIKE`, `IN` | [day2](./day2/) |
| 3 | Sorting & types | `ORDER BY`, `LIMIT`, casts, dates/timestamps | [day3](./day3/) |
| 4 | DML | `INSERT`, `UPDATE`, `DELETE`, `RETURNING` | [day4](./day4/) |
| 5 | DDL & constraints | `CREATE TABLE`, PK/FK/UNIQUE/CHECK | [day5](./day5/) |
| 6 | JOINs | Inner/left joins for inventory & deploy data | [day6](./day6/) |
| 7 | Aggregations | `GROUP BY`, `HAVING`, window functions intro | [day7](./day7/) |
| 8 | Subqueries & CTEs | Readable reports, `EXISTS`, refactoring | [day8](./day8/) |
| 9 | Indexes & EXPLAIN | B-tree basics, plan reading, slow queries | [day9](./day9/) |
| 10 | Transactions & locking | ACID, isolation, deadlocks, idempotent ops | [day10](./day10/) |
| 11 | Schema design | Normalization, naming, audit columns, enums | [day11](./day11/) |
| 12 | Security & roles | `GRANT`, least privilege, connection limits | [day12](./day12/) |
| 13 | Backup & restore | `pg_dump`, PITR concepts, restore drills | [day13](./day13/) |
| 14 | Migrations in CI/CD | Flyway/Liquibase, rollback strategy | [day14](./day14/) |
| 15 | Production operations | Pooling, replicas, monitoring, runbooks | [day15](./day15/) |

## Prerequisites

- Comfortable Linux shell ([Linux handbook](../linux/README.md) Days 1–3).
- Docker basics ([Docker handbook](../docker/README.md) Day 1–3) for the lab database.
- Optional: [AWS Day 17 — RDS](../aws/day17/) after Day 13 for managed Postgres.

## Lab database (all days)

From the `sql/` directory:

```bash
docker compose up -d
docker compose ps

# Connect as handbook user
docker compose exec db psql -U handbook -d handbook

# Or from host if you have psql installed
psql "postgresql://handbook:handbook@localhost:5433/handbook"
```

| Setting | Value |
|---------|--------|
| Host | `localhost` |
| Port | `5433` (mapped from container 5432) |
| Database | `handbook` |
| User / password | `handbook` / `handbook` |

Init scripts in `labs/init/` create the **handbook** schema: environments, services, hosts, deployments, and incidents—data you will query like real ops inventory.

Teardown:

```bash
docker compose down -v   # removes volume — fresh DB next up
```

## How to use this handbook

1. Start **Day 1** and bring up Docker Compose before any lab.
2. Type every query in `psql` or your SQL client—do not only read.
3. Use `\d table_name` and `\d+` in `psql` to inspect schema after each day.
4. Finish each day's **Lab**; compare your results to the sample outputs in the README.
5. Read **DevOps connections**—that is what separates tutorial SQL from job-ready skills.

## Safety

- Lab credentials are **intentionally weak**—never use them outside localhost.
- Never run destructive SQL (`DROP`, `TRUNCATE`, mass `DELETE`) against production without a change ticket and backup.
- Prefer read-only roles for dashboards and on-call ad-hoc queries.

## Design notes

See [DESIGN.md](./DESIGN.md) for curriculum decisions, shared schema rationale, and edge cases discovered during authoring.

**Start here:** [Day 1 — RDBMS basics & setup](./day1/)
