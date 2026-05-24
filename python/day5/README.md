# Day 5 — Strings, Files, pathlib & Reading Log Files

**Goal:** Manipulate text like operators do—split logs, strip noise, read/write configs safely with `pathlib`, and scan application logs for incidents.

**Time:** 4–5 hours

---

## 1. String essentials

```python
line = "  2026-05-24T10:00:01Z ERROR payment timeout  "

line.strip()
line.lower()
line.startswith("2026")
"ERROR" in line

parts = line.split()
# or
level, msg = line.strip().split(" ", 3)[2:4]  # careful with varying fields
```

Raw strings for regex paths:

```python
pattern = r"^\d{4}-\d{2}-\d{2}"
```

---

## 2. f-strings and formatting review

```python
host = "api-1"
print(f"{host!r} load={0.92:.0%}")
```

Join collections for CLI output:

```python
",".join(hosts)
"\n".join(lines)
```

---

## 3. `pathlib.Path` — modern file paths

```python
from pathlib import Path

log_dir = Path("/var/log/myapp")
log_dir.mkdir(parents=True, exist_ok=True)

latest = log_dir / "app.log"
print(latest.name, latest.suffix, latest.parent)

if latest.exists():
    size = latest.stat().st_size
```

| Property / method | Meaning |
|-------------------|---------|
| `/` operator | Join path segments |
| `.exists()` | Path present |
| `.glob("*.log")` | Wildcard listing (Day 10) |
| `.read_text()` | Whole file as str |
| `.write_text()` | Write str |

Prefer `pathlib` over `os.path.join` in new code.

---

## 4. Reading and writing text files

```python
from pathlib import Path

cfg = Path("app.conf")
content = cfg.read_text(encoding="utf-8")

cfg.write_text("timeout=30\n", encoding="utf-8")
```

Context manager (streaming large logs):

```python
with Path("access.log").open(encoding="utf-8", errors="replace") as f:
    for line in f:
        if " 500 " in line:
            print(line.rstrip())
```

`errors="replace"` avoids crashes on binary garbage in mixed logs.

---

## 5. Parsing nginx-style access lines (simplified)

```python
def is_5xx(line: str) -> bool:
    # very naive: status as third-from-last token in quotes
    if '" 5' in line:
        return True
    parts = line.split()
    if len(parts) < 9:
        return False
    try:
        status = int(parts[8])
        return 500 <= status < 600
    except ValueError:
        return False
```

Real parsing should use regex or structured logging—this teaches scanning patterns.

---

## 6. Aggregating log counts

```python
from collections import Counter

counter: Counter[str] = Counter()
with Path("app.log").open() as f:
    for line in f:
        if " ERROR " in line:
            counter["ERROR"] += 1
        elif " WARN " in line:
            counter["WARN"] += 1

for level, count in counter.most_common():
    print(level, count)
```

---

## 7. Rotated logs and glob

```python
for path in sorted(Path("/var/log/myapp").glob("app.log*")):
    print(path, path.stat().st_size)
```

Combine with Day 10 for permissions and large trees.

---

## 8. Lab — Day 5

Work from `python/day5/labs/`.

1. Run `labs/parse_log.py` against `labs/sample_app.log`.
2. Add counting for unique error messages (truncate to 80 chars).
3. Write matching ERROR lines to `labs/errors.out` using `Path.write_text` or line-by-line.
4. Create a `Path` for `labs/config/app.env` with `mkdir`; write `KEY=value` lines.
5. Read config back; build a dict of settings (strip comments `#`).
6. Use `errors="replace"` on a file with a bogus byte sequence—observe no crash.

**Stretch:** Implement a `tail -n` style reader: last N lines without loading entire file into memory (hint: `collections.deque`).

---

## 9. DevOps connections

- **Incidents:** First responder scripts grep logs before centralized SIEM indexing.
- **GitOps:** Read rendered manifests from disk; validate with Python before `kubectl apply`.
- **Encoding:** Always specify `encoding="utf-8"` on text configs—portable across regions.

---

## Quick reference

| Task | API |
|------|-----|
| Path object | `Path("dir") / "file.log"` |
| Read all | `.read_text()` |
| Iterate lines | `.open()` + `for line in f` |
| Strip | `line.strip()` |
| Split | `line.split()` / `.split(",", 1)` |
| Join | `",".join(items)` |

**Next:** [Day 6 — Exceptions & logging](../day6/)
