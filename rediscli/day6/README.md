# Day 6 — Security: ACLs, TLS & Hardening

**Goal:** Configure Redis ACL users, authenticate with `redis-cli`, disable dangerous commands, understand TLS connections, and apply production hardening checklists.

**Time:** 4–5 hours

---

## 1. Threat model (DevOps view)

| Risk | Mitigation |
|------|------------|
| Unauthenticated access | `requirepass` / ACL; bind to private network |
| Data exfiltration | TLS in transit; VPC security groups |
| Accidental `FLUSHALL` | ACL deny; `rename-command` |
| Command injection in apps | Parameterized clients; no shell concat |
| Weak passwords | Secrets manager; rotate ACL passwords |
| Replica impersonation | `masterauth` / ACL for replication user |

Redis should **never** be exposed on the public internet without TLS, strong ACLs, and firewall rules.

---

## 2. ACL (Redis 6+)

Redis 6 replaced single `requirepass` with **ACL users**.

```bash
ACL LIST
ACL USERS
ACL GETUSER default
ACL WHOAMI

# Create app user: read/write keys matching prefix, no admin
ACL SETUSER handbook-app on >app-secret ~handbook:* +@read +@write -@dangerous
ACL SETUSER handbook-app

# Admin user for break-glass
ACL SETUSER handbook-admin on >admin-secret allcommands allkeys

AUTH handbook-app app-secret
SET handbook:day6:secret classified
```

**ACL rule pieces:**

| Token | Meaning |
|-------|---------|
| `on` / `off` | Enable user |
| `>password` | Add password |
| `~pattern` | Allowed key pattern |
| `+@read` | Command category |
| `+set` | Single command |
| `-flushall` | Deny command |
| `allcommands` | Full access (admin only) |

Categories: `@read`, `@write`, `@string`, `@admin`, `@dangerous`, etc. Run `ACL CAT` to list.

Persist ACLs:

```bash
ACL SAVE                    # writes to aclfile
CONFIG GET aclfile
```

---

## 3. `AUTH` and `redis-cli`

```bash
redis-cli -u redis://handbook-app:app-secret@127.0.0.1:6379
export REDISCLI_AUTH='app-secret'   # default user only
redis-cli --user handbook-app -a app-secret PING
```

**Default user:** Disable or restrict in production:

```bash
ACL SETUSER default off
ACL SAVE
```

Ensure another admin user exists before disabling `default`.

---

## 4. `rename-command` and protected mode

In `redis.conf`:

```conf
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG "CONFIG_a8f3c2"
rename-command DEBUG ""
```

Empty string **disables** the command. Document renamed commands in your runbook.

**protected-mode** (default `yes`): binds to localhost if no password and no explicit bind — good for dev; production uses explicit bind + ACL.

---

## 5. TLS

Generate lab certs or use your PKI. Connect with:

```bash
redis-cli -h redis.example.com -p 6380 \
  --tls \
  --cacert ca.crt \
  --cert client.crt \
  --key client.key \
  PING
```

**Kubernetes:** Mount TLS secrets; use `stunnel` or sidecar if legacy client lacks TLS.

**Managed Redis:** AWS/ElastiCache in-transit encryption; download CA bundle from provider docs.

---

## 6. Network & deployment hardening

```conf
bind 10.0.0.5
port 0                    # disable non-TLS port when using tls-port
tls-port 6379
maxclients 10000
timeout 300
tcp-keepalive 60
```

| Check | Action |
|-------|--------|
| Firewall | Allow 6379 only from app subnets |
| No public IP | Private subnets / internal LB |
| Separate users | App vs admin vs replication |
| Audit | Log ACL changes; alert on `CONFIG SET` |
| Updates | Patch Redis with OS image cadence |

---

## 7. DevOps context

- **GitOps:** ACL file or `ACL SETUSER` via Ansible/Terraform null_resource — not hand-edited in prod shell.
- **CI:** Test with read-only ACL user; never production admin creds in pipelines.
- **Compliance:** Encryption at rest (disk/volume) + TLS in transit; log retention for access.
- **Incident:** Rotate ACL passwords; `CLIENT KILL` suspicious sessions; snapshot before forensic changes.

---

## Lab — Day 6

Secure Redis with ACL lab compose:

```bash
cd rediscli/day6/labs
docker compose up -d
bash setup_acl.sh
bash test_acl.sh
```

### Part A: ACL users

Create:

- `handbook-reader` — `+@read`, keys `handbook:*`
- `handbook-writer` — `+@read +@write`, keys `handbook:*`
- Deny `+@dangerous` for both

### Part B: Negative test

As reader, attempt `SET` (should fail) and `GET` (should succeed).

### Part C: ACL persistence

`ACL SAVE` — restart container — verify users survive (`ACL LIST`).

### Part D: rename-command (optional)

Mount `redis-secure.conf` with `FLUSHALL` disabled; confirm `redis-cli FLUSHALL` returns unknown command.

### Challenge

Write an ACL line for a **replication-only** user that can run replication commands but not read application keys (pattern `+psync +replconf +ping` style — look up `ACL CAT` replication-related commands for your version).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `NOAUTH` | `AUTH user pass` or `-u` URL |
| `NOPERM` | ACL missing command category |
| Locked out | Boot with `--aclfile` backup or temp `redis-server --aclfile` recovery |
| TLS handshake fail | Cipher mismatch; check SNI; verify CA chain |

---

## Day 6 checklist

- [ ] Created ACL users with key patterns
- [ ] Used `AUTH` / `--user` with `redis-cli`
- [ ] Understand `rename-command` and protected mode
- [ ] Know how to connect with `--tls`
- [ ] Ran Day 6 lab scripts
- [ ] Completed replication-user ACL challenge

**Next:** [Day 7 — Production operations](../day7/)
