# Day 2 — Control Flow: if/for/while, Truthiness, enumerate, range

**Goal:** Branch and loop over hosts, ports, and retries; use truthiness for config flags; iterate cleanly with `enumerate` and `range`.

**Time:** 3–4 hours

---

## 1. Comparisons and boolean logic

```python
status_code = 503
healthy = status_code < 400

if status_code == 200:
    level = "ok"
elif status_code < 500:
    level = "client_error"
else:
    level = "server_error"

# Chained comparisons
if 1 <= port <= 65535:
    print(f"Valid port {port}")
```

| Operator | Meaning |
|----------|---------|
| `==`, `!=` | Equality |
| `<`, `<=`, `>`, `>=` | Ordering |
| `and`, `or`, `not` | Boolean combine |
| `in` | Membership (`"prod" in env`) |

---

## 2. Truthiness — the DevOps gate

These are **falsy**: `False`, `0`, `0.0`, `""`, `[]`, `{}`, `set()`, `None`.

```python
config_value = os.environ.get("FEATURE_FLAG")  # may be None or ""

if config_value:
    enable_feature()
else:
    log.info("Feature disabled — empty or unset")
```

**Pitfall:** `"false"` as a string is **truthy**. Parse explicitly:

```python
def env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")
```

---

## 3. `if` patterns for operations

```python
role = "db"
dry_run = True

if role in ("web", "api"):
  target_group = "frontend"
elif role == "db":
  target_group = "data"
else:
  target_group = "misc"

# Ternary
action = "skip" if dry_run else "apply"
```

Match/case (Python 3.10+) for many discrete states:

```python
match status_code:
    case 200:
        print("healthy")
    case 429:
        print("rate limited — backoff")
    case _:
        print(f"unexpected {status_code}")
```

---

## 4. `for` loops over collections

```python
hosts = ["web1", "web2", "web3"]

for host in hosts:
    print(f"ping {host}")

for line in open("/var/log/nginx/access.log"):
    if " 500 " in line:
        print(line.rstrip())
```

Prefer **not** to mutate a list while iterating over it—build a new list instead.

---

## 5. `enumerate` — index + value

Essential for numbered rollout steps and parallel arrays:

```python
servers = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]

for i, ip in enumerate(servers, start=1):
    print(f"Wave {i}: deploy to {ip}")

for idx, host in enumerate(hosts):
    print(f"{idx}: {host}")   # default start=0
```

With `zip` for paired data:

```python
names = ["web1", "web2"]
ips = ["10.0.0.10", "10.0.0.11"]
for name, ip in zip(names, ips, strict=True):
    print(f"{name} -> {ip}")
```

`strict=True` (3.10+) raises if lengths differ—catch inventory bugs early.

---

## 6. `range` — numeric iteration

```python
for port in range(8080, 8084):      # 8080, 8081, 8082, 8083
    probe(port)

for attempt in range(3):            # 0, 1, 2
    print(f"retry {attempt}")

for i in range(0, 10, 2):           # step by 2
    print(i)
```

**Do not** use `range` to index a list when you only need values—iterate the list directly.

---

## 7. `while` — retries and polling

```python
import time

deadline = time.monotonic() + 120
interval = 5

while time.monotonic() < deadline:
    if service_healthy():
        break
    time.sleep(interval)
else:
    # while-else: ran without break
    raise TimeoutError("service not healthy after 120s")
```

| Pattern | Use |
|---------|-----|
| `while True` + `break` | Consumer loops, menu CLIs |
| `while condition` | Poll until state |
| `while-else` | Detect exhausted retries without flag variable |

---

## 8. `break`, `continue`, `pass`

```python
for host in fleet:
    if host in maintenance:
        continue
    if not ping(host):
        print(f"skip unreachable {host}")
        continue
    deploy(host)
```

`pass` is a no-op placeholder for unfinished branches.

---

## 9. Lab — Day 2

Work from `python/day2/labs/`.

1. Run `labs/check_port.py` — extend `PORTS` and observe branching.
2. In `labs/retry_loop.py`, change `MAX_ATTEMPTS` and `BACKOFF_SEC`; watch truthiness on `success`.
3. Write a loop that prints `enumerate` over 5 fake canary hosts with wave numbers starting at 1.
4. Implement `env_bool()` and test with `export DRY_RUN=true` / `false` / unset.
5. Parse a multiline string of hosts (one per line); skip blanks and lines starting with `#`.
6. Add a `while` poll: sleep 1s, decrement timeout, exit when a marker file exists.

**Stretch:** Use `match/case` on HTTP status families in `check_port.py`.

---

## 10. DevOps connections

- **Rolling deploys:** `enumerate` maps to wave numbers; combine with sleep between waves.
- **Retries:** Exponential backoff belongs in `while` or `for` + `time.sleep` (Day 6 adds structured logging).
- **Config flags:** Never assume empty env means false—document and parse.

---

## Quick reference

| Task | Pattern |
|------|---------|
| Loop hosts | `for h in hosts:` |
| With index | `for i, h in enumerate(hosts, 1):` |
| Numeric | `for i in range(n):` |
| Retry | `for attempt in range(max):` |
| Falsy check | `if value:` |
| Skip item | `continue` |

**Next:** [Day 3 — Functions, scope, *args/**kwargs](../day3/)
