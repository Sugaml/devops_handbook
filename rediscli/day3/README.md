# Day 3 — Server Introspection, Memory & Persistence

**Goal:** Read `INFO` and `CONFIG`, understand memory limits and eviction, configure RDB/AOF, and use `SLOWLOG` / `CLIENT LIST` for operations.

**Time:** 4–5 hours

---

## 1. The `INFO` command

`INFO` returns metrics as `section:key=value` lines.

```bash
redis-cli INFO server
redis-cli INFO memory
redis-cli INFO stats
redis-cli INFO replication
redis-cli INFO persistence
redis-cli INFO clients
redis-cli INFO keyspace
redis-cli INFO all | less
```

**High-signal fields (operations):**

| Section | Field | Meaning |
|---------|-------|---------|
| `server` | `redis_version` | Running version |
| `memory` | `used_memory_human` | Total RAM used |
| `memory` | `maxmemory` | Cap (0 = unlimited) |
| `stats` | `instantaneous_ops_per_sec` | Current throughput |
| `stats` | `keyspace_hits` / `keyspace_misses` | Cache effectiveness |
| `persistence` | `aof_enabled` | AOF on/off |
| `replication` | `role` | `master` or `slave`/`replica` |

Parse in scripts:

```bash
redis-cli INFO memory | grep '^used_memory_human:'
redis-cli --raw INFO stats | awk -F: '/^total_commands_processed:/{print $2}'
```

---

## 2. `CONFIG GET` / `SET` / `REWRITE`

```bash
CONFIG GET maxmemory
CONFIG GET maxmemory-policy
CONFIG GET save
CONFIG GET appendonly
CONFIG GET dir
CONFIG GET dbfilename

# Runtime change (lost on restart unless persisted)
CONFIG SET maxmemory 256mb
CONFIG SET maxmemory-policy allkeys-lru

# Persist to redis.conf (if server started with a writable config file)
CONFIG REWRITE
```

**Eviction policies** (when `maxmemory` reached):

| Policy | Behavior |
|--------|----------|
| `noeviction` | Writes fail with OOM errors |
| `allkeys-lru` | Evict any key (LRU approx) |
| `volatile-lru` | Evict keys with TTL only |
| `allkeys-lfu` | Least frequently used (Redis 4+) |
| `volatile-ttl` | Evict keys with shortest TTL |

**Production default:** Set `maxmemory` to ~70–80% of container limit; choose policy matching cache vs session data.

---

## 3. Memory analysis

```bash
MEMORY USAGE handbook:day3:bigkey
MEMORY STATS
MEMORY DOCTOR                    # heuristic advice (Redis 4+)
redis-cli --bigkeys              # scan for large keys (slow on prod — off-peak)
redis-cli --memkeys              # Redis 7.4+ memory per key sampling
```

Object encoding (advanced):

```bash
OBJECT ENCODING handbook:day3:hashkey
OBJECT IDLETIME handbook:day3:hashkey
```

---

## 4. Persistence: RDB vs AOF

| | RDB (snapshot) | AOF (append log) |
|---|----------------|------------------|
| **Format** | Compact binary dump | Replay of write commands |
| **Durability** | Point-in-time; may lose last minutes | `everysec` ≈ 1s loss; `always` fsync each write |
| **Recovery** | Fast load | Slower replay; may need rewrite |
| **Disk I/O** | Periodic fork + write | Continuous append |

**RDB triggers** (`save` directive):

```bash
CONFIG GET save
# Default example: save 3600 1 300 100 60 10000
# = save if 1 change in 3600s OR 100 changes in 300s OR ...
```

Manual snapshot:

```bash
SAVE                  # blocking — avoid on prod master
BGSAVE                # background fork
LASTSAVE              # Unix time of last successful RDB
```

**AOF:**

```bash
CONFIG GET appendonly
CONFIG SET appendonly yes
CONFIG GET appendfsync    # always | everysec | no
BGREWRITEAOF              # compact AOF file
```

Lab compose already runs `--appendonly yes`. Inspect:

```bash
docker compose exec redis ls -la /data
docker compose exec redis redis-cli CONFIG GET dir
```

---

## 5. Clients and slow queries

```bash
CLIENT LIST
CLIENT ID
CLIENT GETNAME
CLIENT SETNAME handbook-lab
CLIENT KILL ID <id>              # careful in production
CLIENT PAUSE 5000                # maintenance window (Redis 3+)

SLOWLOG GET 10
SLOWLOG LEN
SLOWLOG RESET

CONFIG GET slowlog-log-slower-than   # microseconds threshold
CONFIG GET slowlog-max-len
```

**`MONITOR`:** Streams every command to your session. **Never leave running in production** — huge overhead. Use only in dev for seconds.

```bash
# Terminal A
redis-cli MONITOR
# Terminal B — run a few commands, then Ctrl+C A
```

---

## 6. Database sizing

```bash
DBSIZE                   # keys in current DB
INFO keyspace            # per-DB counts if multiple DBs used
SELECT 1                 # switch DB (discouraged in cluster; prefer key prefixes)
DBSIZE
SELECT 0
```

---

## 7. DevOps context

- **Kubernetes:** Set memory requests/limits; align `maxmemory` with cgroup limit minus overhead.
- **Backups:** Copy RDB/AOF files during `BGSAVE` completion or use managed service snapshots.
- **Upgrades:** Read release notes; test `INFO server` version in staging; check ACL/RDB format changes.
- **Alerts:** `used_memory_rss` vs limit, `blocked_clients`, `rejected_connections`, replication lag.

---

## Lab — Day 3

Start from `rediscli/`:

```bash
docker compose up -d redis
cd day3
redis-cli < labs/day3_ops.redis
```

### Part A: INFO drill

Document `redis_version`, `used_memory_human`, `maxmemory`, and `role` from your instance.

### Part B: Slowlog

```bash
redis-cli CONFIG SET slowlog-log-slower-than 0
redis-cli DEBUG SLEEP 0.01    # if DEBUG allowed; else run a tight loop script
# Alternative: CONFIG SET slowlog-log-slower-than 1 then many SETs in pipeline
redis-cli SLOWLOG GET 5
redis-cli CONFIG SET slowlog-log-slower-than 10000
```

Note: `DEBUG` may be disabled via `rename-command` in hardened installs (Day 6).

### Part C: BGSAVE

```bash
redis-cli SET handbook:day3:persist test
redis-cli BGSAVE
redis-cli LASTSAVE
docker compose exec redis ls -l /data/dump.rdb
```

Restart container and verify key survives:

```bash
docker compose restart redis
redis-cli GET handbook:day3:persist
```

### Part D: maxmemory experiment

```bash
redis-cli CONFIG SET maxmemory 1mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
# Fill memory with many keys until evictions occur (script in labs/fill_memory.sh)
bash labs/fill_memory.sh
redis-cli INFO stats | grep evicted
redis-cli CONFIG SET maxmemory 0
```

### Challenge

Write a one-liner shell script `handbook_redis_health.sh` that exits 0 only if `PING` is PONG and `used_memory` < 90% of `maxmemory` (or skip ratio check if `maxmemory` is 0).

---

## Troubleshooting

| Symptom | Investigation |
|---------|----------------|
| Writes fail `OOM` | `INFO memory`; raise limit or eviction policy |
| Disk full | `dir` path; AOF rewrite; rotate logs |
| Slow commands | `SLOWLOG GET`; `LATENCY DOCTOR` (Day 7) |
| Empty after restart | Persistence off or wrong volume mount |

---

## Day 3 checklist

- [ ] Queried `INFO` sections relevant to ops
- [ ] Explained RDB vs AOF tradeoffs
- [ ] Ran `BGSAVE` and verified RDB file
- [ ] Used `SLOWLOG` and understand `MONITOR` risk
- [ ] Tested `maxmemory` + eviction briefly
- [ ] Completed health script challenge

**Next:** [Day 4 — Replication](../day4/)
