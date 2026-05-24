# Day 7 Capstone Report — Checkout Degraded

**Investigator:** _your name_  
**Date:** _YYYY-MM-DD_  
**Instance:** `127.0.0.1:6383` (lab)

## 1. Symptoms

_What users/apps experienced (timeouts, 500s, elevated latency)._

## 2. Evidence

| Check | Result |
|-------|--------|
| `PING` | |
| `used_memory` / `maxmemory` | |
| `evicted_keys` | |
| `DBSIZE` | |
| `SLOWLOG` | |
| Largest keys (`--bigkeys` or `MEMORY USAGE`) | |
| Hot key pattern | |

```bash
# Paste relevant command output snippets below


```

## 3. Root cause hypothesis

_Why did checkout fail? Tie evidence to session blobs, eviction, or hot key._

## 4. Remediation (immediate)

- [ ] _e.g. Delete `handbook:day7:session:*` after app fix_
- [ ] _Raise maxmemory / scale vertically_
- [ ] _Add TTL to session keys in application_

## 5. Prevention (longer term)

- [ ] Memory alerts at 80% `maxmemory`
- [ ] Key naming standards + mandatory TTL for cache/session keys
- [ ] Review `maxmemory-policy` for workload
- [ ] Load test checkout path against Redis

## 6. Commands reference

_List the 5 `redis-cli` commands you would run first in a real incident._
