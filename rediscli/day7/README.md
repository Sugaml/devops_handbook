# Day 7 — Production Operations, Pipelines & Capstone

**Goal:** Operate Redis under load: pipelining, `redis-cli --stat` / `--bigkeys`, latency analysis, incident playbooks, and a capstone scenario tying Days 1–6 together.

**Time:** 5–7 hours

---

## 1. Pipelining and batching

Without pipeline, each command waits for a round trip:

```bash
# Slow: 10,000 round trips
for i in $(seq 1 10000); do redis-cli SET "handbook:day7:k:$i" "$i"; done
```

**Pipeline mode** (`redis-cli --pipe` or app-level pipeline):

```bash
# Generate Redis protocol
(
  for i in $(seq 1 10000); do
    echo "SET handbook:day7:pipe:$i $i"
  done
) | redis-cli --pipe

# Count replies
echo "SET handbook:day7:one 1" | redis-cli --pipe | tail -1
```

**Lua** for atomic multi-step logic (same slot in Cluster):

```bash
redis-cli EVAL "return redis.call('SET', KEYS[1], ARGV[1])" 1 handbook:day7:lua test
```

Production: prefer app client pipelines; cap batch size to avoid timeouts.

---

## 2. Live monitoring CLI tools

```bash
redis-cli --stat
# keys, memory, clients, ops/sec — refreshes until Ctrl+C

redis-cli --latency
redis-cli --latency-history
redis-cli LATENCY DOCTOR
redis-cli LATENCY LATEST

redis-cli --bigkeys -i 0.1
redis-cli --memkeys -i 0.1    # Redis 7.4+
```

| Tool | When to use |
|------|-------------|
| `--stat` | Quick dashboard during incident |
| `--bigkeys` | Memory spike investigation (off-peak) |
| `--latency` | Network or slow command diagnosis |
| `LATENCY DOCTOR` | Human-readable latency report |

---

## 3. Pub/Sub and blocking ops (ops awareness)

```bash
SUBSCRIBE deploys
PUBLISH deploys "v2.3.1 rolled out"
PSUBSCRIBE logs:*

# Blocking list pop — ties up connection
BLPOP queue 0
```

**Impact:** Many blocked clients or `MONITOR` sessions hurt capacity. Track `blocked_clients` in `INFO`.

---

## 4. Incident playbook templates

### Symptom: App timeouts to Redis

```bash
redis-cli PING
redis-cli INFO clients | grep -E 'connected_clients|blocked_clients'
redis-cli INFO stats | grep instantaneous_ops_per_sec
redis-cli SLOWLOG GET 20
redis-cli --latency-history
```

Check: network ACL, max connections, slow queries, primary down (Day 4), cluster `CLUSTERDOWN` (Day 5).

### Symptom: Memory maxed

```bash
redis-cli INFO memory
redis-cli --bigkeys
redis-cli CONFIG GET maxmemory-policy
```

Actions: extend memory, fix leak/TTL, eviction policy tune, delete bad keys (with change ticket).

### Symptom: Replication lag

```bash
redis-cli -p 6381 INFO replication
# master_link_status, offset lag
```

Actions: network fix, reduce write burst, check disk on replica during full sync.

### Symptom: Auth failures after deploy

```bash
redis-cli ACL LIST
redis-cli ACL WHOAMI
# Compare K8s secret version vs app env
```

---

## 5. Backup and restore drill

```bash
# Trigger snapshot
redis-cli BGSAVE
redis-cli LASTSAVE

# Copy RDB (lab)
docker compose exec redis cp /data/dump.rdb /data/dump.rdb.bak

# Restore: stop redis, replace dump.rdb, start (lab only — coordinate in prod)
```

**AOF rewrite:**

```bash
redis-cli BGREWRITEAOF
redis-cli INFO persistence | grep aof_rewrite
```

---

## 6. Integration patterns (reference)

| Pattern | Redis feature |
|---------|---------------|
| Cache aside | `GET` / `SET` + TTL |
| Distributed lock | `SET key token NX EX` + Lua compare-del |
| Leader election | Redlock or Consul — not raw `SET` alone |
| Rate limit | `INCR` + `EXPIRE` |
| Job queue | `LPUSH`/`BRPOP` or Streams |
| Geo (if needed) | `GEOADD` / `GEORADIUS` |

---

## 7. Capstone scenario — "Checkout degraded"

**Story:** E-commerce checkout errors spiked. Metrics show Redis timeouts. You have read-only access via `redis-cli`.

**Your tasks:**

1. Confirm connectivity (`PING`, `INFO server`)
2. Check memory and eviction (`INFO memory`, `stats`)
3. Find hot keys (`--bigkeys` sample or `SCAN` + `MEMORY USAGE`)
4. Review slow log (`SLOWLOG GET`)
5. If replica in path — check lag (Day 4)
6. Document findings + recommended actions (scale, TTL fix, command tuning, fail over)

Use the capstone lab data:

```bash
cd rediscli/day7/labs
docker compose up -d
bash seed_capstone.sh
bash investigate.sh    # skeleton — you fill analysis
```

---

## Lab — Day 7

### Part A: Pipeline benchmark

Compare loop `SET` vs `--pipe` for 5000 keys (time both).

### Part B: `--stat` observation

Run `redis-cli --stat` while executing `seed_capstone.sh` in another terminal.

### Part C: Latency

```bash
redis-cli --latency
# In another terminal: redis-cli DEBUG SLEEP 0.05  # if allowed
redis-cli LATENCY DOCTOR
```

### Part D: Capstone report

Complete `labs/capstone_report.md` with sections: Symptoms, Evidence, Root cause hypothesis, Remediation, Prevention.

### Challenge

Add a **Prometheus-style** text export sketch: shell script parsing `INFO memory` and `INFO stats` into `redis_used_memory_bytes` and `redis_keyspace_hits_total` lines (no exporter install required).

---

## 7-day graduation checklist

- [ ] Day 1: CLI fluency, strings, TTL
- [ ] Day 2: All core types + `SCAN`
- [ ] Day 3: `INFO`, persistence, memory limits
- [ ] Day 4: Replication lab
- [ ] Day 5: Cluster create/check
- [ ] Day 6: ACL hardening
- [ ] Day 7: Pipeline, monitoring, capstone report

---

## Further reading

- [Redis commands](https://redis.io/commands/)
- [ACL documentation](https://redis.io/docs/management/security/acl/)
- [Redis Cluster specification](https://redis.io/docs/reference/cluster-spec/)
- [Operational best practices](https://redis.io/docs/management/optimization/)

**Handbook complete.** Revisit days as you adopt Sentinel, Cluster, or managed Redis in production.
