# Day 4 — Lists, Dicts, Sets, Comprehensions & Parsing Data

**Goal:** Model inventory, metrics, and API payloads with core collections; parse CSV/JSON-like structures; use comprehensions for concise transforms.

**Time:** 4–5 hours

---

## 1. Lists — ordered fleets

```python
hosts = ["web1", "web2", "web3"]
hosts.append("web4")
hosts.extend(["web5", "web6"])

first = hosts[0]
last = hosts[-1]
subset = hosts[1:3]      # web2, web3 — slice copy

if "web2" in hosts:
    hosts.remove("web2")
```

| Method | Effect |
|--------|--------|
| `.append(x)` | Add one item |
| `.extend(iter)` | Add many |
| `.pop()` | Remove and return last |
| `.sort()` | In-place sort |
| `sorted(hosts)` | New sorted list |

---

## 2. Dicts — maps and records

```python
server = {
    "name": "web-prod-01",
    "ip": "10.0.1.10",
    "role": "web",
    "labels": {"env": "prod", "tier": "frontend"},
}

server["ip"]
server.get("zone", "unknown")

server["version"] = "2.1.0"
del server["labels"]["tier"]   # careful KeyError if missing
```

Iterate:

```python
for name, ip in server.items():
    print(name, ip)

for key in server:
    ...
```

Merge (3.9+):

```python
defaults = {"retries": 3, "timeout": 30}
overrides = {"timeout": 60}
cfg = defaults | overrides
```

---

## 3. Sets — uniqueness and membership

```python
open_ports = {22, 80, 443}
open_ports.add(8080)

required = {80, 443}
missing = required - open_ports      # set difference
both = required & open_ports           # intersection
```

Use sets to dedupe host lists:

```python
unique_hosts = list(dict.fromkeys(hosts))  # preserves order
# or
unique_hosts = sorted(set(hosts))
```

---

## 4. List comprehensions

```python
ips = ["10.0.0.1", "10.0.0.2", "bad", "10.0.0.4"]
valid = [ip for ip in ips if ip.startswith("10.")]
upper_names = [h.upper() for h in hosts]

# Nested — flatten AZ -> instances
by_az = [["i-1", "i-2"], ["i-3"]]
flat = [iid for group in by_az for iid in group]
```

Keep comprehensions **readable**—if logic spans multiple filters, use a plain `for` loop.

---

## 5. Dict and set comprehensions

```python
instances = [
    {"id": "i-1", "state": "running"},
    {"id": "i-2", "state": "stopped"},
]

running = {i["id"] for i in instances if i["state"] == "running"}

name_to_ip = {h["name"]: h["ip"] for h in inventory}
```

---

## 6. Parsing JSON (API responses)

```python
import json

raw = '{"region": "us-east-1", "count": 3}'
data = json.loads(raw)
print(data["region"])

payload = {"hosts": hosts, "dry_run": True}
print(json.dumps(payload, indent=2, sort_keys=True))
```

From file:

```python
with open("inventory.json") as f:
    inv = json.load(f)
```

---

## 7. Parsing CSV (inventory exports)

```python
import csv

with open("hosts.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["hostname"], row["ip"])
```

Write:

```python
with open("out.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["hostname", "ip"])
    writer.writeheader()
    writer.writerows(rows)
```

---

## 8. Simple line-based parsing

```python
def parse_hosts(text: str) -> list[dict[str, str]]:
    hosts = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, ip = line.split(",", maxsplit=1)
        hosts.append({"name": name.strip(), "ip": ip.strip()})
    return hosts
```

---

## 9. Lab — Day 4

Work from `python/day4/labs/`.

1. Run `labs/parse_inventory.py` with sample data; add three hosts.
2. Filter inventory to `role == "web"` using a list comprehension.
3. Build a `dict` mapping hostname → ip from parsed data.
4. Given two host lists (yesterday/today), use sets to find **added** and **removed** hosts.
5. Load `labs/sample_inventory.json` (create if missing) with `json.load`; print sorted keys.
6. Export filtered web hosts to CSV with `csv.DictWriter`.

**Stretch:** Parse `KEY=value` lines from a fake `.env` into a dict (skip comments).

---

## 10. DevOps connections

- **Terraform/Ansible:** State and inventory are JSON/YAML—Python glues them between tools.
- **API pagination:** Accumulate pages in a list, then dedupe with sets.
- **Immutable transforms:** Prefer new dicts (`|`, comprehensions) over mutating shared globals in pipelines.

---

## Quick reference

| Task | Pattern |
|------|---------|
| List comp | `[x for x in items if cond]` |
| Dict comp | `{k: v for ...}` |
| JSON in | `json.loads(s)` / `json.load(f)` |
| JSON out | `json.dumps(obj)` |
| CSV rows | `csv.DictReader` |
| Dedupe | `set(items)` |

**Next:** [Day 5 — Strings, files & pathlib](../day5/)
