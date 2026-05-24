# Day 5 — Redis Cluster: Slots, Topology & `redis-cli --cluster`

**Goal:** Understand hash slots, create a minimal cluster, use `redis-cli -c` and cluster subcommands, and recognize `MOVED`/`ASK` redirects.

**Time:** 5–6 hours (cluster startup takes a few minutes)

---

## 1. Why Cluster?

Single Redis instance is limited by **one CPU thread** and **RAM on one host**. **Redis Cluster** shards data across masters using **16,384 hash slots**.

```
Client                    Cluster
  │                         │
  │── SET user:1 ──────────►│ slot 9842 → Master A
  │◄── MOVED 9842 ip:port ──│ (if wrong node)
  │── SET user:1 ──────────►│ Master A (retry)
```

| Concept | Detail |
|---------|--------|
| **Slot** | Hash slot 0–16383; each key maps via `CRC16(key) mod 16384` |
| **Master** | Owns slot ranges; handles writes for those slots |
| **Replica** | Hot standby per master |
| **Minimum prod** | 3 masters + 3 replicas (6 nodes) |
| **Minimum lab** | 3 masters (no replicas) — not HA |

**Hash tags:** Keys with `{tag}` share a slot — `user:{42}:profile` and `user:{42}:cart` co-locate.

```bash
SET user:{42}:name alice
SET user:{42}:orders 3
# Both hash to same slot because only {42} is hashed
```

---

## 2. Cluster-aware CLI

```bash
redis-cli -c -p 7000    # -c enables cluster redirects (follow MOVED)
CLUSTER INFO
CLUSTER NODES
CLUSTER SLOTS
CLUSTER KEYSLOT handbook:day5:key
CLUSTER COUNTKEYSINSLOT 5942
```

**Creating a cluster** (lab):

```bash
cd rediscli/day5/labs
docker compose up -d
bash create_cluster.sh
```

---

## 3. `redis-cli --cluster` toolbox

```bash
# Create cluster (example — script uses your node list)
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  --cluster-replicas 0

# Check health
redis-cli --cluster check 127.0.0.1:7000

# Add node / reshard (production maintenance)
redis-cli --cluster add-node NEW_IP:PORT EXISTING_IP:PORT
redis-cli --cluster reshard EXISTING_IP:PORT
```

---

## 4. Multi-key operations rules

| Command | Cluster rule |
|---------|--------------|
| `MGET` / `DEL` multiple keys | All keys must be same slot (use hash tags) |
| `MULTI` transaction | All keys in same slot |
| `SCAN` | Per-node; use `SCAN` on each master |
| `DBSIZE` | Sum per node; not global single command |

```bash
# Works — same hash tag
MGET user:{42}:a user:{42}:b

# May fail with CROSSSLOT
MGET user:42:a user:99:b
```

---

## 5. Failover (overview)

1. Master fails; replicas detect via gossip.
2. Replica promoted if majority of masters agree.
3. Slots reassigned to new master.
4. Clients refresh slot map (via redirects or `CLUSTER SLOTS`).

**Managed services** hide this; you still need **hash tag** discipline in app code.

---

## 6. Cluster vs Sentinel vs single instance

| Mode | Sharding | HA | Complexity |
|------|----------|-----|------------|
| Single + replica | No | Manual/Sentinel | Low |
| Sentinel | No | Automatic failover | Medium |
| Cluster | Yes | Automatic per shard | High |
| Cloud (ElastiCache cluster mode) | Yes | Managed | $$$, lower ops |

---

## 7. DevOps context

- **Client libraries** must be cluster-aware (Jedis, go-redis, redis-py `RedisCluster`).
- **Helm:** `bitnami/redis-cluster` or cloud-specific charts.
- **Migrations:** Resharding is online but plan capacity; watch `cluster_state`.
- **Backups:** Per-shard RDB or coordinated tools; not one `SAVE` for whole cluster.

---

## Lab — Day 5

```bash
cd rediscli/day5/labs
docker compose up -d
# Wait ~10s for nodes healthy
bash create_cluster.sh
bash verify_cluster.sh
```

### Part A: Slot inspection

```bash
redis-cli -c -p 7000 CLUSTER KEYSLOT handbook:day5:foo
redis-cli -c -p 7000 CLUSTER KEYSLOT 'user:{42}:id'
```

### Part B: Cross-slot experiment

```bash
redis-cli -c -p 7000 MSET handbook:day5:a 1 handbook:day5:b 2
# Often OK — different slots may still work as separate commands in cluster mode depending on client
redis-cli -c -p 7000 MGET handbook:day5:a handbook:day5:b
```

### Part C: Node failure (advanced)

`docker compose stop redis-node-2` — run `redis-cli --cluster check 127.0.0.1:7000` and observe `cluster_state`. Restore node and heal.

### Challenge

List three application changes required when moving from **single Redis** to **Cluster** (connection, multi-key, Lua scripts).

---

## Troubleshooting

| Error | Meaning |
|-------|---------|
| `CLUSTERDOWN` | Not all slots covered; quorum lost |
| `MOVED` | Wrong node; use `redis-cli -c` or update client |
| `ASK` | Temporary import during resharding |
| `CROSSSLOT` | Multi-key op spans slots — add hash tags |
| `TRYAGAIN` | Temporary cluster state change — retry |

---

## Day 5 checklist

- [ ] Explained 16384 slots and hash tags
- [ ] Created 3-node lab cluster
- [ ] Used `redis-cli -c` and `CLUSTER NODES`
- [ ] Ran `--cluster check`
- [ ] Completed migration challenge list

**Next:** [Day 6 — Security](../day6/)
