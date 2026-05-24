# Day 1 — Setup, REPL, Variables, Types & First Script

**Goal:** Install Python 3, use the interactive REPL, understand core types and f-strings, and write a small DevOps-oriented script you can run from the shell.

**Time:** 3–4 hours

---

## 1. Why Python for DevOps?

| Use case | Why Python |
|----------|------------|
| Glue automation | Call APIs, parse JSON/YAML, wrap shell tools |
| CI/CD pipelines | Jenkins shared libs, custom GitHub Actions steps |
| Cloud SDKs | boto3, google-cloud-*, azure-sdk |
| Config & inventory | Transform Terraform outputs into Ansible vars |
| Observability | Parse logs, emit metrics, alert routing |

Python trades raw speed for **readability** and a huge ecosystem. Most ops scripts are I/O-bound (SSH, HTTP, disk)—Python is a strong default.

---

## 2. Install and verify Python 3

### macOS

```bash
brew install python@3.12
python3 --version    # Python 3.12.x
which python3
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version
```

### Check pip and venv (Day 7 goes deeper)

```bash
python3 -m pip --version
python3 -m venv /tmp/test-venv && rm -rf /tmp/test-venv
```

**Convention:** Use `python3` explicitly in docs and shebangs so you never accidentally invoke Python 2 on older systems.

---

## 3. The REPL — rapid experimentation

Start the **Read–Eval–Print Loop**:

```bash
python3
```

```python
>>> 2 + 2
4
>>> hostname = "web-prod-01"
>>> f"Checking {hostname}"
'Checking web-prod-01'
>>> exit()   # or Ctrl-D
```

**DevOps tip:** Use the REPL to test `json.loads()`, regex patterns, or date math before pasting into a playbook or pipeline.

Run a one-liner without entering the REPL:

```bash
python3 -c "import platform; print(platform.node())"
```

---

## 4. Variables, assignment, naming

Python variables are **references** to objects (no `var`/`let` keywords).

```python
environment = "production"
replica_count = 3
is_draining = False

# Multiple assignment
host, port = "10.0.1.42", 443
```

| Style | Example | Notes |
|-------|---------|-------|
| `snake_case` | `server_name` | Standard for variables and functions |
| `UPPER_SNAKE` | `MAX_RETRIES` | Module-level constants |
| Avoid | `x`, `tmp` | Use descriptive names in ops code |

Constants are a convention only—nothing stops reassignment:

```python
DEFAULT_TIMEOUT_SEC = 30
```

---

## 5. Core types for operations work

| Type | Example | Typical DevOps use |
|------|---------|-------------------|
| `str` | `"us-east-1"` | Regions, hostnames, log lines |
| `int` | `8080` | Ports, PIDs, exit codes |
| `float` | `99.9` | Percentages, latency |
| `bool` | `True` | Feature flags, health checks |
| `None` | `None` | Missing optional config |

```python
region: str = "eu-west-1"
port: int = 22
healthy: bool = True
last_error: str | None = None   # Python 3.10+ union syntax
```

Type hints are optional at runtime but help teammates and static checkers (`mypy`).

### Truthiness (preview of Day 2)

Empty strings, zero, empty containers, and `None` are **falsy**:

```python
>>> bool("")
False
>>> bool("ok")
True
```

---

## 6. f-strings — formatting for humans and logs

Prefer **f-strings** (Python 3.6+) over `%` or `.format()` for clarity:

```python
service = "api"
version = "2.4.1"
instances = 6

message = f"Deploy {service} v{version} to {instances} nodes"
# Deploy api v2.4.1 to 6 nodes

# Alignment and numbers
for i in range(1, 4):
    print(f"pod-{i:02d}  CPU={12.5:5.1f}%")
```

```python
# Expressions inside braces
hosts = ["web1", "web2"]
print(f"Fleet size: {len(hosts)}, first={hosts[0]!r}")
```

Use `!r` for `repr()`-style debugging output (quotes visible).

---

## 7. Your first script — structure and shebang

Create `labs/hello_devops.py`:

```python
#!/usr/bin/env python3
"""Print a deployment banner — Day 1 lab."""

def main() -> None:
    app = "payments-api"
    env = "staging"
    build = "a1b2c3d"
    print(f"[{env}] {app} build={build} ready for smoke tests")

if __name__ == "__main__":
    main()
```

Run it:

```bash
cd python/day1
chmod +x labs/hello_devops.py
python3 labs/hello_devops.py
./labs/hello_devops.py   # needs executable bit + shebang
```

| Piece | Purpose |
|-------|---------|
| Shebang | OS finds `python3` when executed directly |
| `main()` | Keeps importable modules clean |
| `if __name__ == "__main__"` | Code runs only when executed, not when imported |

---

## 8. Reading environment and simple I/O

Ops scripts often read **environment variables** (12-factor style):

```python
import os

db_host = os.environ.get("DB_HOST", "localhost")
print(f"Connecting to {db_host}")
```

```bash
export DB_HOST=db.internal
python3 labs/hello_devops.py
```

---

## 9. Lab — Day 1

Work from `python/day1/labs/`.

1. Verify `python3 --version` is 3.10+.
2. In the REPL, create variables for `hostname`, `ip`, `role` (e.g. `web`); print an f-string inventory line.
3. Run `labs/hello_devops.py`; change app/env/build to match your lab naming.
4. Extend `labs/server_status.py`: set `cpu_percent`, `mem_percent`, `disk_percent`; print a one-line status with aligned numbers.
5. Add a type hint to every variable in `server_status.py` and run the script again.
6. Export `APP_ENV=production` and read it in a copy of hello script via `os.environ`.

**Stretch:** Print the same status line in JSON using `import json` and a dict (preview of Day 4).

---

## 10. DevOps connections

- **Pipelines:** Almost every CI image includes Python; scripts gate merges and deployments.
- **Idempotency:** Scripts should be safe to re-run; print clear messages so logs explain what happened.
- **Shebang + `python3 -m`:** Prefer `python3 -m pip` over bare `pip` to target the interpreter you intend (Day 7).

---

## Quick reference

| Task | Command / snippet |
|------|-------------------|
| Version | `python3 --version` |
| REPL | `python3` |
| Run script | `python3 script.py` |
| One-liner | `python3 -c "..."` |
| f-string | `f"{var}"` |
| Env var | `os.environ.get("KEY", "default")` |

**Next:** [Day 2 — Control flow (if/for/while)](../day2/)
