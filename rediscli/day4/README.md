# Day 4 — Replication & Read Replicas

**Goal:** Configure primary/replica topology, verify replication with `INFO` and `ROLE`, send read traffic to replicas, and handle common failover concepts.

**Time:** 4–5 hours

---

## 1. Replication model

```
┌─────────────┐     replication stream      ┌─────────────┐
│   Primary   │ ──────────────────────────► │   Replica   │
│  (master)   │   async by default          │  (read-only)│
└─────────────┘                             └─────────────┘
       ▲                                           │
       │ writes                                    │ reads (optional)
   Applications                                  Apps / cache warmers
```

- **One primary** accepts writes (single-shard topology).
- **Replicas** copy the primary's dataset; Redis 7 uses `REPLICAOF` (legacy docs say `SLAVEOF`).
- Replication is **asynchronous** — replicas can lag; design apps accordingly.
- **Sentinel / Operator** handle automatic failover (overview below; deep dive in managed services).

---

## 2. Key commands

```bash
ROLE                          # master | slave + offsets
INFO replication
REPLICAOF host port           # become replica of host
REPLICAOF NO ONE              # promote to primary (manual failover step)
CONFIG GET replica-read-only
CONFIG SET replica-read-only yes
```

On primary:

```bash
INFO replication
# connected_slaves, master_repl_offset
```

On replica:

```bash
INFO replication
# master_link_status: up, slave_repl_offset, lag indicators
```

---

## 3. Start the replication lab

From `rediscli/day4/labs/`:

```bash
docker compose up -d
docker compose ps
```

Topology:

| Service | Port | Role |
|---------|------|------|
| `redis-primary` | 6380 | Primary |
| `redis-replica` | 6381 | Replica of primary |

```bash
redis-cli -p 6380 PING
redis-cli -p 6381 PING
redis-cli -p 6380 SET handbook:day4:seed replicated
redis-cli -p 6381 GET handbook:day4:seed
redis-cli -p 6381 ROLE
```

Replica should be read-only:

```bash
redis-cli -p 6381 SET handbook:day4:fail test
# (error) READONLY You can't write against a read only replica.
```

---

## 4. Replication lifecycle

### Initial sync

1. Replica connects; primary may `BGSAVE` RDB and stream + buffer writes.
2. Full resync if replica too far behind or checksum mismatch.

### Ongoing

- Primary propagates command stream (or partial resync with backlog).
- Check `master_link_status` on replica during incidents.

### Manual promotion (break-glass)

```bash
redis-cli -p 6381 REPLICAOF NO ONE
redis-cli -p 6381 ROLE    # now master
# Re-point apps to 6381; fix old primary or rebuild as replica
```

**Production:** Use **Redis Sentinel** (3+ sentinels) or **Redis Cluster** / cloud HA — not manual promotion alone.

---

## 5. Sentinel (conceptual)

Sentinels monitor primaries and vote on failover:

```bash
# Typical sentinel port 26379
redis-cli -p 26379 SENTINEL masters
redis-cli -p 26379 SENTINEL replicas mymaster
```

Kubernetes patterns:

- **Helm bitnami/redis** with sentinel sidecars
- **ElastiCache / Memorystore** — failover is managed
- **Operator** (OT-Container-Kit, Spotahome) encodes topology in CRDs

Day 5 covers **Cluster** (sharding), which is a different HA model than primary/replica.

---

## 6. Read scaling patterns

| Pattern | Notes |
|---------|-------|
| Read from replica | Stale reads possible; OK for dashboards |
| Sticky sessions to primary | Strong consistency for session writes |
| Cache aside | App writes primary; reads replica with version checks |

```bash
# Compare offset lag (approximate)
redis-cli -p 6380 INFO replication | grep master_repl_offset
redis-cli -p 6381 INFO replication | grep slave_repl_offset
```

---

## 7. DevOps context

- **Connection strings:** Separate `REDIS_WRITE_URL` and `REDIS_READ_URL` in apps.
- **Backups:** Snapshot from replica to reduce primary I/O (`BGSAVE` on replica).
- **Secrets:** Replication auth via `masterauth` / ACL (Day 6).
- **Monitoring:** `connected_slaves`, replication offset lag, `master_link_down_since_seconds`.

---

## Lab — Day 4

```bash
cd rediscli/day4/labs
docker compose up -d
bash verify_replication.sh
```

### Part A: Verify sync

Write 100 keys on primary; sample 10 on replica with `MGET` or loop.

### Part B: Lag observation

```bash
redis-cli -p 6380 DEBUG POPULATE 10000 handbook:day4:pop 20
redis-cli -p 6381 DBSIZE
```

(`DEBUG POPULATE` may be disabled in hardened configs.)

### Part C: Failover drill (lab only)

1. Stop primary: `docker compose stop redis-primary`
2. Promote replica: `redis-cli -p 6381 REPLICAOF NO ONE`
3. Write new key on promoted node
4. Restore primary and reconfigure as replica (optional advanced step)

### Challenge

Document a **runbook outline** (5 bullets) for "primary unreachable" including: app impact, Sentinel vs manual, data loss window, and who reconfigures DNS/K8s Service.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Replica empty | `REPLICAOF` wrong host/firewall; check `master_link_status` |
| `READONLY` on app writes | Client pointed at replica URL |
| Full resync loop | Network instability; `repl-backlog-size`; check disk |
| Split brain | Use odd Sentinel count; quorum; avoid dual primaries |

---

## Day 4 checklist

- [ ] Drew primary/replica diagram for your stack
- [ ] Ran Day 4 compose lab on ports 6380/6381
- [ ] Verified `ROLE` and read-only replica
- [ ] Practiced `REPLICAOF NO ONE` promotion in lab
- [ ] Understand Sentinel vs Cluster vs managed HA
- [ ] Completed failover runbook challenge

**Next:** [Day 5 — Redis Cluster](../day5/)
