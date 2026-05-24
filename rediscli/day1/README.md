# Day 1 — Redis Fundamentals & `redis-cli` Basics

**Goal:** Understand what Redis is, why DevOps teams run it, start a lab instance, and use `redis-cli` for connection, strings, and key lifecycle.

**Time:** 3–4 hours

---

## 1. Why Redis in DevOps?

| Use case | How Redis helps |
|----------|-----------------|
| Application cache | Sub-millisecond reads; offload databases |
| Session store | Fast TTL-based user sessions |
| Rate limiting | Counters with `INCR` + `EXPIRE` |
| Job queues | Lists / Streams for background workers |
| Pub/Sub | Lightweight event fan-out (not durable messaging) |
| Feature flags / config | Fast key lookups at scale |

Redis is an **in-memory data structure server**. Persistence (RDB/AOF) is optional—Day 3 covers when to enable it.

```
App / API ──► redis-cli or client library ──► Redis (TCP 6379)
                      │
                      └── Single-threaded command processor (per shard in Cluster)
```

**Not a replacement for:**

- PostgreSQL (complex queries, transactions, reporting)
- Kafka/RabbitMQ (durable, replayable message backlogs)
- S3 (large object storage)

---

## 2. Core concepts

| Term | Meaning |
|------|---------|
| **Instance** | One `redis-server` process |
| **Database** | Logical namespace `0`–`15` (default 16); selected with `-n` / `SELECT` |
| **Key** | Unique name for a value (string, list, hash, …) |
| **Value** | Data stored at a key; type determines commands |
| **TTL** | Time-to-live; key auto-deletes when expired |
| **Command** | Single operation (`SET`, `GET`, `INFO`, …) |

Keys are **binary-safe strings**. Convention: `service:entity:id` (e.g. `api:user:42`).

---

## 3. Start the lab instance

From `rediscli/`:

```bash
docker compose up -d redis
docker compose ps
docker compose exec redis redis-cli PING
```

Expected: `PONG`.

Host-side (after `brew install redis` or `apt install redis-tools`):

```bash
redis-cli -h 127.0.0.1 -p 6379 PING
```

---

## 4. `redis-cli` connection options

```bash
redis-cli --help | head -40

# Common flags
redis-cli -h 127.0.0.1 -p 6379          # host and port
redis-cli -n 1                           # database index (default 0)
redis-cli -a 'secret'                    # password (prefer REDISCLI_AUTH env)
redis-cli --no-auth-warning              # suppress "Using a password" warning
redis-cli -u redis://:secret@127.0.0.1:6379/0   # URL form (Redis 6+)
```

**Interactive vs one-shot:**

```bash
redis-cli                    # REPL: type commands, see replies
redis-cli SET foo bar        # single command, exit
redis-cli <<EOF
SET handbook:day1:ping ok
GET handbook:day1:ping
EOF
```

**Output modes:**

```bash
redis-cli GET handbook:day1:ping           # quoted string reply
redis-cli --raw GET handbook:day1:ping     # raw bytes (scripts, binary)
redis-cli --csv KEYS 'handbook:day1:*'     # CSV (automation)
```

---

## 5. Essential commands (Day 1)

### Connectivity & server

```bash
PING                       # health check
ECHO "hello"               # echo test
QUIT                       # close connection (interactive)
```

### Strings

```bash
SET handbook:day1:name "DevOps Handbook"
GET handbook:day1:name
SET handbook:day1:counter 0
INCR handbook:day1:counter
GET handbook:day1:counter    # "1"
APPEND handbook:day1:name " v1"
GET handbook:day1:name
```

`SET` options you'll use often:

```bash
SET handbook:day1:temp value EX 60    # expire in 60 seconds
SET handbook:day1:temp2 value NX      # only if key does not exist
SET handbook:day1:temp2 value XX      # only if key exists
```

### Key metadata

```bash
TYPE handbook:day1:name      # string
EXISTS handbook:day1:name    # 1 or 0
TTL handbook:day1:temp        # seconds remaining; -1 no expiry; -2 missing
DEL handbook:day1:name       # delete one key
UNLINK handbook:day1:temp    # async delete (preferred on large values, Redis 4+)
```

### Listing keys (dev only)

```bash
KEYS handbook:day1:*
```

**Production warning:** `KEYS` scans the entire keyspace and blocks the server. Use `SCAN` (Day 2).

---

## 6. Interactive REPL tips

Inside `redis-cli`:

| Input | Effect |
|-------|--------|
| `↑` / `↓` | Command history |
| `Ctrl+C` | Cancel long command |
| `Ctrl+D` | Exit |
| `HELP @string` | Help for string commands (Redis 7) |
| `CLEAR` | Clear screen |

Run Redis commands from a file:

```bash
redis-cli < labs/day1_basics.redis
```

---

## 7. DevOps context

- **Health checks:** Kubernetes `exec` probes often run `redis-cli ping` (or TCP on 6379).
- **12-factor:** Connection URL via env (`REDIS_URL`); no hard-coded passwords in images.
- **Observability:** `PING` proves TCP + auth; app-level checks should `GET`/`SET` a canary key.
- **Naming:** Prefix keys by service and environment (`prod:checkout:cart:uuid`).

---

## Lab — Day 1

Prerequisites: `docker compose up -d redis` from `rediscli/`.

### Part A: Connection

```bash
redis-cli PING
redis-cli INFO server | head -5
redis-cli CONFIG GET databases
```

### Part B: String exercises

```bash
redis-cli SET handbook:day1:env lab
redis-cli GET handbook:day1:env
redis-cli SET handbook:day1:visits 0
redis-cli INCR handbook:day1:visits
redis-cli INCRBY handbook:day1:visits 9
redis-cli GET handbook:day1:visits
```

### Part C: TTL

```bash
redis-cli SET handbook:day1:session token123 EX 120
redis-cli TTL handbook:day1:session
redis-cli PTTL handbook:day1:session
# Wait 2 minutes or: redis-cli DEL handbook:day1:session
```

### Part D: Cleanup

```bash
redis-cli KEYS 'handbook:day1:*'
redis-cli DEL handbook:day1:env handbook:day1:visits
```

Or run the lab file:

```bash
cd rediscli/day1
redis-cli < labs/day1_basics.redis
```

### Challenge

Run two terminals: Terminal A `redis-cli SUBSCRIBE alerts` (preview of pub/sub). Terminal B `redis-cli PUBLISH alerts "deploy started"`. Observe the message in A. Press `Ctrl+C` in A to unsubscribe.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Could not connect` | `docker compose ps`; port 6379 not in use by another Redis |
| `NOAUTH Authentication required` | Pass `-a` or set `REDISCLI_AUTH` (Day 6) |
| `OOM command not allowed` | Instance out of memory; check `INFO memory` (Day 3) |
| Wrong database | `redis-cli -n 0` vs app using `-n 1` |

---

## Day 1 checklist

- [ ] Explained Redis vs SQL and message queues
- [ ] Started lab Redis with Docker Compose
- [ ] Used `redis-cli` interactive and one-shot modes
- [ ] `SET`/`GET`/`INCR`/`EXPIRE`/`TTL`/`DEL`
- [ ] Understand why `KEYS` is for dev only
- [ ] Completed challenge (pub/sub peek)

**Next:** [Day 2 — Data structures & SCAN](../day2/)
