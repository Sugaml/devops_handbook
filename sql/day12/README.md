# Day 12 — Security: Roles, GRANT & Connection Hygiene

**Goal:** Create database roles with least privilege, grant SELECT/INSERT/UPDATE appropriately, separate admin from app and read-only users, and apply connection limits.

**Time:** 4 hours

---

## 1. PostgreSQL roles

In PostgreSQL, **roles** can login (users) or be groups (granted to other roles).

```sql
-- As superuser handbook (lab only) or postgres
CREATE ROLE app_reader NOLOGIN;
CREATE ROLE app_writer NOLOGIN;
CREATE ROLE oncall_ro LOGIN PASSWORD 'change-me-ro' CONNECTION LIMIT 5;
CREATE ROLE ci_deploy LOGIN PASSWORD 'change-me-ci' CONNECTION LIMIT 3;

GRANT app_reader TO oncall_ro;
GRANT app_writer TO ci_deploy;
```

Production: passwords from vault; `CONNECTION LIMIT` prevents one service from exhausting max_connections.

---

## 2. Schema and table grants

```sql
GRANT USAGE ON SCHEMA public TO app_reader, app_writer;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO app_reader;

GRANT SELECT, INSERT, UPDATE ON deployments, deployment_steps TO app_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_writer;

-- No DELETE on prod for ci_deploy — rollback via new deploy
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM ci_deploy;
```

Verify:

```sql
\du
\dp deployments
```

---

## 3. Column-level grants (rare)

```sql
GRANT SELECT (id, version, status, started_at) ON deployments TO oncall_ro;
-- Hide deployed_by PII if needed
```

Prefer views for complex column masking.

---

## 4. Read-only views for on-call

```sql
CREATE VIEW v_open_incidents AS
SELECT i.id, i.title, i.severity, s.name AS service, i.opened_at
FROM incidents i
JOIN services s ON s.id = i.service_id
WHERE i.resolved_at IS NULL;

GRANT SELECT ON v_open_incidents TO oncall_ro;
REVOKE SELECT ON incidents FROM oncall_ro;  -- if previously granted
```

---

## 5. Row Level Security (RLS) preview

```sql
ALTER TABLE deployments ENABLE ROW LEVEL SECURITY;

CREATE POLICY deployments_env_isolation ON deployments
FOR SELECT
TO app_reader
USING (environment_id = current_setting('app.environment_id')::int);
```

App sets `SET app.environment_id = 2` per connection—multi-tenant SaaS pattern.

---

## 6. Network and auth layers

| Layer | Control |
|-------|---------|
| Security group / firewall | Only app subnets → 5432 |
| TLS | `sslmode=require` in connection string |
| IAM auth | RDS IAM database authentication |
| Secrets | Vault, AWS Secrets Manager rotation |

Connection string (app):

```
postgresql://ci_deploy:***@localhost:5433/handbook?sslmode=disable
```

Lab disables SSL; production requires it.

---

## 7. Dangerous privileges

Never grant to app roles:

- `SUPERUSER`, `CREATEDB`, `CREATEROLE`
- `TRUNCATE`, `DROP` on production schemas
- Broad `ALL PRIVILEGES`

Use migration role separate from runtime role.

---

## 8. Lab — Day 12

From `sql/day12/labs/`:

1. Run `roles_grants.sql` as handbook user.
2. Connect as `oncall_ro`; SELECT from `v_open_incidents`; try `DELETE FROM deployments` — expect permission denied.
3. Connect as `ci_deploy`; INSERT a deployment; try UPDATE on `services` — denied if not granted.
4. List roles and memberships: `\du+`
5. Document a grant matrix (role × table × privileges) for your real org template.
6. Set `CONNECTION LIMIT 1` on a test role; open two sessions—second fails.

**Stretch:** Enable RLS on a table with a policy for `environment_id`.

---

## 9. DevOps connections

- **Rotation:** App creds in K8s Secret; rotate without code change via external secret operator.
- **Break-glass:** DBA admin role MFA + logged session— not shared app password.
- **Compliance:** SOC2 expects least privilege evidence—export `\dp` regularly.

---

## Quick reference

| Task | SQL |
|------|-----|
| Create role | `CREATE ROLE name LOGIN PASSWORD '...';` |
| Grant select | `GRANT SELECT ON table TO role;` |
| Revoke | `REVOKE DELETE ON table FROM role;` |
| Default privs | `ALTER DEFAULT PRIVILEGES ...` |
| List privs | `\dp` |

**Next:** [Day 13 — Backup, restore & recovery drills](../day13/)
