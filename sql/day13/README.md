# Day 13 — Backup, Restore & Point-in-Time Recovery

**Goal:** Take logical backups with `pg_dump`, restore to a fresh database, understand physical backups and PITR concepts on RDS, and run a recovery drill checklist.

**Time:** 4–5 hours

---

## 1. Backup types

| Type | Tool | Use |
|------|------|-----|
| Logical | `pg_dump`, `pg_dumpall` | Schema + data SQL/custom format; portable |
| Physical | Base backup + WAL archive | Full PITR; managed by RDS/automation |
| Snapshot | EBS / RDS snapshot | Fast restore entire instance |

DevOps owns **restore drills**, not just backup jobs.

---

## 2. pg_dump — logical backup

Custom format (compressed, parallel restore):

```bash
docker compose exec db pg_dump -U handbook -Fc handbook > /tmp/handbook-$(date +%Y%m%d).dump
```

Plain SQL:

```bash
docker compose exec db pg_dump -U handbook --no-owner --no-acl handbook > /tmp/handbook.sql
```

Schema only:

```bash
docker compose exec db pg_dump -U handbook -s handbook > /tmp/handbook-schema.sql
```

Single table:

```bash
docker compose exec db pg_dump -U handbook -t deployments handbook > /tmp/deployments.sql
```

---

## 3. pg_restore

Create empty database and restore:

```bash
docker compose exec db createdb -U handbook handbook_restore
docker compose exec -T db pg_restore -U handbook -d handbook_restore < /tmp/handbook-20240524.dump
docker compose exec db psql -U handbook -d handbook_restore -c "\dt"
```

From host with file on disk:

```bash
pg_restore -h localhost -p 5433 -U handbook -d handbook_restore handbook.dump
```

Parallel jobs:

```bash
pg_restore -j 4 -U handbook -d handbook_restore handbook.dump
```

---

## 4. Restore drill checklist

1. **RTO/RPO** documented: how much data loss is acceptable?
2. Backup job succeeded (check cron/Kubernetes CronJob logs).
3. Restore to **isolated** instance—not over production.
4. Run smoke queries: row counts, latest deployment id.
5. App connectivity test with read-only user.
6. Record duration; update runbook.

```sql
SELECT 'deployments' AS tbl, COUNT(*) FROM deployments
UNION ALL SELECT 'hosts', COUNT(*) FROM hosts;
```

---

## 5. WAL and PITR (conceptual)

PostgreSQL writes WAL before data files. Continuous archiving enables restore to **any timestamp** (within retention).

Managed RDS:

- Automated backups + retention window
- Restore to new instance → `restore-time` parameter
- Test quarterly—snapshots expire silently if never used

---

## 6. Dangerous operations

```sql
-- Never run on prod without backup
DROP DATABASE handbook;
TRUNCATE deployments CASCADE;
```

Keep **pre-migration dump** before Flyway upgrade (Day 14).

---

## 7. Backup automation sketch (Kubernetes CronJob)

```yaml
# Conceptual — pg_dump sidecar or dedicated job
command: ["sh", "-c", "pg_dump $DATABASE_URL | gzip | aws s3 cp - s3://backups/handbook/$(date +%F).sql.gz"]
```

Encrypt at rest; restrict S3 IAM; test restore from S3 monthly.

---

## 8. Lab — Day 13

From `sql/day13/labs/`:

1. Run `backup_restore.sh` from `sql/day13/labs/` (or manual commands in README).
2. Compare row counts: `handbook` vs `handbook_restore`.
3. Delete a row in restore DB only; confirm prod unchanged.
4. Dump schema-only; inspect for GRANT statements (`--no-acl` if sharing externally).
5. Write RTO/RPO for a fictional payments service (1 hour RTO, 5 min RPO)—which backup type fits?
6. Document restore steps in 5 bullets for your team's runbook template.

**Stretch:** Restore single table `deployments` into temp table using `pg_restore -t`.

---

## 9. DevOps connections

- **RDS:** [AWS Day 17](../../aws/day17/) — snapshot before major upgrade.
- **Git ≠ backup:** Schema in git; **data** still needs pg_dump/replication.
- **Compliance:** GDPR delete requests need backup retention policy alignment.

---

## Quick reference

| Task | Command |
|------|---------|
| Dump custom | `pg_dump -Fc dbname > file.dump` |
| Dump SQL | `pg_dump dbname > file.sql` |
| Restore | `pg_restore -d dbname file.dump` |
| Schema only | `pg_dump -s dbname` |
| Verify | Row counts + spot checks |

**Next:** [Day 14 — Migrations in CI/CD](../day14/)
