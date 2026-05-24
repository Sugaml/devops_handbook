# Redis CLI for DevOps — 7-Day Handbook

A hands-on path from your first `redis-cli PING` to production operations: replication, clustering, ACLs, persistence, and on-call troubleshooting. Every day includes commands you can run against the included Docker lab stack.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Redis fundamentals, `redis-cli` basics, strings & keys | [day1](./day1/) |
| 2 | Data structures, TTL, and safe key iteration (`SCAN`) | [day2](./day2/) |
| 3 | Server introspection, memory, persistence (RDB/AOF) | [day3](./day3/) |
| 4 | Replication and read replicas | [day4](./day4/) |
| 5 | Redis Cluster — slots, topology, resharding | [day5](./day5/) |
| 6 | Security — ACLs, TLS, dangerous commands | [day6](./day6/) |
| 7 | Production ops, pipelines, troubleshooting, capstone | [day7](./day7/) |

## Prerequisites

- Comfortable with Linux shell and Docker ([Docker handbook](../docker/README.md) Day 1 is enough).
- 2 GB+ RAM free for cluster labs (Day 5).
- Optional: [Network handbook](../network/README.md) for ports and DNS context.

## Lab environment

From this directory:

```bash
# Single-node Redis (Days 1–3, 6–7)
docker compose up -d redis

# Verify
redis-cli -h 127.0.0.1 -p 6379 PING
# or inside the container:
docker compose exec redis redis-cli PING
```

Day 4 and Day 5 use additional compose files under each day's `labs/` folder.

Install `redis-cli` on your host (recommended for learning):

```bash
# macOS
brew install redis

# Ubuntu/Debian
sudo apt install -y redis-tools

redis-cli --version
```

## How to use this handbook

1. Start the lab Redis before each session (`docker compose up -d redis`).
2. Type every command yourself; use `redis-cli --help` when unsure.
3. Complete each day's **Lab** before advancing.
4. On Day 7, keep a personal cheat sheet of the `INFO`, `SCAN`, and `redis-cli --cluster` flags you use at work.

## Design notes

- Examples target **Redis 7.x** semantics (ACL-first, improved cluster tools).
- Production callouts highlight what to enable or disable in real fleets.
- Labs use isolated key prefixes (`handbook:dayN:*`) so you can `FLUSHDB` safely in dev.
