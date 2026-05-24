# Redis CLI Handbook — Design Notes

## Curriculum arc

| Day | Skill level | Focus |
|-----|-------------|--------|
| 1 | Beginner | Mental model, `redis-cli`, strings |
| 2 | Beginner+ | Data structures, `SCAN`, TTL patterns |
| 3 | Intermediate | Ops metrics, persistence, memory |
| 4 | Intermediate | HA building block — replication |
| 5 | Advanced | Horizontal scale — Cluster |
| 6 | Advanced | Security baseline for production |
| 7 | Professional | Incidents, performance, capstone |

## Lab port map

| Port | Stack |
|------|--------|
| 6379 | Main `rediscli/docker-compose.yml` |
| 6380 / 6381 | Day 4 primary / replica |
| 7000–7002 | Day 5 cluster nodes |
| 6382 | Day 6 ACL lab |
| 6383 | Day 7 capstone |

## Decisions

- **Redis 7 Alpine** — small images; matches current ACL/cluster CLI behavior.
- **Key prefix `handbook:dayN:`** — safe cleanup without touching other local Redis data.
- **Day 5: 3 masters, 0 replicas** — minimum nodes to teach slots; production needs 6+ nodes for HA.
- **`protected-mode no` in labs** — Docker bridge access; never copy to public internet without ACL/TLS.
- **`rename-command` on FLUSHALL/FLUSHDB** in Day 6 — common production pattern demonstrated in lab.

## Edge cases noted in labs

- `DEBUG` / `DEBUG POPULATE` may be disabled when commands are renamed.
- `redis-cli --cluster create` requires all nodes reachable; script waits for `PING`.
- `fill_memory.sh` stops at 50k keys to avoid runaway local OOM.
- macOS `xargs` lacks `-r`; Day 2 cleanup uses `xargs` only on Linux or manual `DEL`.

## User feedback

_(Add notes here as you extend the handbook.)_
