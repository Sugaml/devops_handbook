# Day 2 — Data Structures, TTL Patterns & `SCAN`

**Goal:** Use lists, sets, sorted sets, and hashes confidently; expire keys safely; iterate with `SCAN` instead of `KEYS`.

**Time:** 4–5 hours

---

## 1. Type overview

| Type | Typical use | Example key |
|------|-------------|-------------|
| **string** | Cache, counters, JSON blob | `api:response:abc` |
| **list** | Queues, recent events | `worker:queue:emails` |
| **set** | Unique tags, online users | `chat:room:9:members` |
| **hash** | Object fields | `user:42` → name, email |
| **zset** | Leaderboards, priority queues | `deploy:priority` |
| **stream** | Durable event log (intro) | `events:deploys` |

Check type anytime: `TYPE key`.

---

## 2. Lists — FIFO queues

```bash
LPUSH handbook:day2:queue job1 job2 job3
RPUSH handbook:day2:queue job4
LRANGE handbook:day2:queue 0 -1
LPOP handbook:day2:queue          # job3 (LPUSH + LPOP = stack; use RPOP for FIFO)
RPOP handbook:day2:queue
LLEN handbook:day2:queue
BLPOP handbook:day2:queue 5       # block up to 5s waiting for element
```

**DevOps pattern:** Worker does `BRPOP queue 0` in a loop; producer `LPUSH`es tasks. For at-least-once with ack, consider **Streams** (Redis 5+) or a proper queue (SQS, RabbitMQ).

---

## 3. Sets — uniqueness

```bash
SADD handbook:day2:tags redis devops cache
SADD handbook:day2:tags redis          # duplicate ignored
SMEMBERS handbook:day2:tags
SISMEMBER handbook:day2:tags devops     # 1
SCARD handbook:day2:tags

SADD handbook:day2:allowed 10.0.0.0/8 192.168.1.5
SINTER handbook:day2:tags handbook:day2:allowed   # empty unless overlap
SUNION handbook:day2:tags handbook:day2:allowed
```

---

## 4. Sorted sets (zset) — score ordering

```bash
ZADD handbook:day2:leaderboard 100 alice 250 bob 180 carol
ZRANGE handbook:day2:leaderboard 0 -1 WITHSCORES
ZREVRANGE handbook:day2:leaderboard 0 2 WITHSCORES   # top 3
ZRANK handbook:day2:leaderboard bob
ZINCRBY handbook:day2:leaderboard 50 bob
```

Scores are **floats**. Same member cannot appear twice; `ZADD` updates score.

---

## 5. Hashes — field maps

```bash
HSET handbook:day2:host:web1 ip 10.0.1.10 role web env staging
HGET handbook:day2:host:web1 ip
HGETALL handbook:day2:host:web1
HMGET handbook:day2:host:web1 ip role
HINCRBY handbook:day2:host:web1 restarts 1
HDEL handbook:day2:host:web1 env
HLEN handbook:day2:host:web1
```

Prefer hashes over many string keys when fields belong to one object (`HGETALL` vs dozens of `GET`s).

---

## 6. Strings as JSON / structured blobs

```bash
SET handbook:day2:deploy '{"id":"d-1","status":"running"}'
GET handbook:day2:deploy
# Apps often use RedisJSON module in production; plain string + app parse works too
```

---

## 7. TTL and expiration patterns

```bash
SET handbook:day2:lock token NX EX 30     # distributed lock sketch (use Redlock lib in prod)
TTL handbook:day2:lock
PERSIST handbook:day2:lock                # remove TTL
EXPIRE handbook:day2:lock 60
EXPIREAT handbook:day2:lock 1893456000    # Unix timestamp

# Inspect keys expiring soon (Redis 7.4+ KEYSPEC varies; common pattern):
# SCAN + TTL per key in scripts
```

| Command | Purpose |
|---------|---------|
| `EXPIRE key sec` | Set TTL in seconds |
| `PEXPIRE key ms` | Milliseconds |
| `TTL` / `PTTL` | Time remaining |
| `PERSIST` | Remove expiry |

---

## 8. `SCAN` — production-safe iteration

`SCAN` cursor-based; does not block like `KEYS`.

```bash
SCAN 0 MATCH handbook:day2:* COUNT 100
# Returns: cursor "6" and batch of keys — repeat with new cursor until 0

HSCAN handbook:day2:host:web1 0
SSCAN handbook:day2:tags 0
ZSCAN handbook:day2:leaderboard 0
```

Shell loop example:

```bash
cursor=0
while true; do
  reply=$(redis-cli SCAN "$cursor" MATCH 'handbook:day2:*' COUNT 50)
  cursor=$(echo "$reply" | head -1)
  echo "$reply" | tail -n +2
  [ "$cursor" = "0" ] && break
done
```

---

## 9. Streams (brief)

```bash
XADD handbook:day2:events * service api action deploy status ok
XREAD COUNT 1 STREAMS handbook:day2:events 0
XLEN handbook:day2:events
```

Use streams when you need **consumer groups**, message IDs, and trimming (`MAXLEN`).

---

## Lab — Day 2

```bash
cd rediscli/day2
redis-cli < labs/day2_structures.redis
```

### Part A: Incident queue (list)

Simulate three alerts; process with `RPOP` until empty.

### Part B: Allowlist (set)

Add three CIDRs/IPs to a set; verify `SISMEMBER`.

### Part C: Deploy priority (zset)

Add three services with scores; print top 2 with `ZREVRANGE`.

### Part D: Host record (hash)

Store hostname, ip, region; increment `check_fails` twice with `HINCRBY`.

### Part E: SCAN cleanup

```bash
# Delete all handbook:day2:* keys via SCAN (practice cursor loop or):
redis-cli --scan --pattern 'handbook:day2:*' | xargs -r redis-cli DEL
```

### Challenge

Implement a **rate limit** sketch: key `handbook:day2:rl:user42` with `INCR`; on first hit `EXPIRE 60`; if count > 10, reject (script logic in your shell). Reset and test 11 requests.

---

## Troubleshooting

| Issue | Cause / fix |
|-------|-------------|
| `WRONGTYPE Operation` | Command doesn't match key type; `TYPE key` |
| Empty `LPOP` | List empty; use `BLPOP` or check `LLEN` |
| `SCAN` returns duplicates | Normal; dedupe in application |
| Huge `HGETALL` | Hash has thousands of fields; use `HSCAN` |

---

## Day 2 checklist

- [ ] Created list, set, zset, hash examples
- [ ] Used `NX`/`EX` TTL patterns
- [ ] Iterated with `SCAN` (not `KEYS`)
- [ ] Ran `labs/day2_structures.redis`
- [ ] Completed rate-limit challenge

**Next:** [Day 3 — INFO, memory & persistence](../day3/)
