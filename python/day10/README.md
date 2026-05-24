# Day 10 — os, sys, pathlib, Permissions & glob for System Ops

**Goal:** Inspect and manipulate the local environment like an operator—paths, env vars, exit codes, file modes, and wildcard scans across log and config trees.

**Time:** 4–5 hours

---

## 1. `sys` — interpreter and exit

```python
import sys

print(sys.version)
print(sys.platform)       # darwin, linux, win32
print(sys.argv)           # CLI args
print(sys.executable)     # python3 path

sys.exit(0)               # success
sys.exit("fatal error")   # stderr message + code 1
```

Pipe-friendly:

```python
if not sys.stdin.isatty():
    data = sys.stdin.read()
```

---

## 2. `os.environ` and process identity

```python
import os

home = os.environ.get("HOME", "/tmp")
path = os.environ["PATH"]   # KeyError if missing

os.environ["DEPLOY_ENV"] = "staging"   # affects child processes only

uid = os.getuid()           # Unix only
gid = os.getgid()
print(os.getlogin())
```

| Variable | Typical use |
|----------|-------------|
| `HOME` | Config paths |
| `USER` | Audit logs |
| `PATH` | Finding binaries |
| `TMPDIR` | Scratch space |

---

## 3. `pathlib` review for system paths

```python
from pathlib import Path

etc = Path("/etc")
nginx_conf = etc / "nginx" / "nginx.conf"

resolved = Path("logs/../logs/app.log").resolve()
relative = resolved.relative_to(Path.cwd())
```

---

## 4. File permissions and metadata

```python
import os
import stat
from pathlib import Path

p = Path("deploy.sh")
mode = p.stat().st_mode
print(oct(stat.S_IMODE(mode)))   # e.g. 0o755

# Add executable bit for owner/group/world
p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# Or precise
p.chmod(0o755)
```

| Octal | Meaning |
|-------|---------|
| `0o644` | rw-r--r-- file |
| `0o755` | rwxr-xr-x script |
| `0o600` | rw------- secret |

Check ownership (Unix):

```python
st = p.stat()
print(st.st_uid, st.st_gid)
```

---

## 5. `glob` — find logs and artifacts

```python
from pathlib import Path

log_root = Path("/var/log/myapp")
for path in sorted(log_root.glob("**/*.log")):
    if path.is_file():
        print(path, path.stat().st_size)

# Single directory non-recursive
for conf in Path("etc").glob("*.conf"):
    print(conf.name)
```

| Pattern | Matches |
|---------|---------|
| `*.log` | Suffix in one dir |
| `**/*.json` | Recursive |
| `app.log.*` | Rotated logs |

---

## 6. Walking trees with `os.walk`

```python
import os

for dirpath, dirnames, filenames in os.walk("/var/log"):
    for name in filenames:
        if not name.endswith(".log"):
            continue
        full = os.path.join(dirpath, name)
        ...
```

Prefer `pathlib` `rglob` for new code; `os.walk` remains common in legacy tooling.

---

## 7. Disk usage snapshot (stdlib)

```python
import shutil

usage = shutil.disk_usage("/")
print(
    f"total={usage.total // (2**30)}GiB "
    f"used={usage.used // (2**30)}GiB "
    f"free={usage.free // (2**30)}GiB"
)
```

---

## 8. Cross-platform notes

| Feature | Linux/macOS | Windows |
|---------|-------------|---------|
| `os.getuid()` | Yes | Not available |
| `chmod` | Full | Limited model |
| Symlinks | `Path.symlink_to` | May need admin |

Use `sys.platform.startswith("win")` to branch sparingly.

---

## 9. Lab — Day 10

Work from `python/day10/labs/`.

1. Run `disk_report.py` on `.` and on `/tmp`.
2. Extend report: list five largest `*.py` files under `python/day10/labs` via `glob`.
3. Create `labs/staging/deploy.sh` with mode `0o755`; verify executable bit in octal.
4. Write `0o600` secrets file `labs/staging/secret.env`; confirm others cannot read (Unix).
5. Print sorted `os.environ` keys matching `PATH`, `HOME`, `USER`, `SHELL`.
6. Exit with code 2 when path argument does not exist.

**Stretch:** Implement `--min-size-mb` filter for glob results.

---

## 10. DevOps connections

- **Hardening:** Config files `0640`, keys `0600`, scripts `0755`—automation enforces with Python after template render.
- **Log rotation:** Glob `app.log*` and ship files older than N days to object storage.
- **Pre-flight:** Disk and permission checks before destructive deploy scripts run.

---

## Quick reference

| Task | API |
|------|-----|
| Exit code | `sys.exit(n)` |
| Env | `os.environ.get("K")` |
| Path join | `Path("a") / "b"` |
| chmod | `path.chmod(0o755)` |
| Glob | `path.glob("**/*.log")` |
| Disk | `shutil.disk_usage(path)` |

**Next:** Continue your DevOps journey—apply Days 1–10 to real pipelines, then explore cloud SDKs and testing in advanced tracks.
