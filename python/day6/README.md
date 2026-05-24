# Day 6 — Exceptions, try/except/finally & Logging Basics

**Goal:** Handle failures in scripts without silent crashes; use `try/except/else/finally` correctly; emit structured logs with the `logging` module for CI and on-call.

**Time:** 4–5 hours

---

## 1. Why exceptions beat error codes in Python

Many C-style APIs return `-1` on failure. Python raises **exceptions**—flow jumps to the nearest matching `except` block.

```python
def read_port(path: str) -> int:
    with open(path) as f:
        return int(f.read().strip())
# FileNotFoundError, ValueError possible
```

Callers choose: handle, re-raise, or let the script die with traceback.

---

## 2. try / except / else / finally

```python
from pathlib import Path

def load_config(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"config missing: {path}")
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}") from exc
    else:
        # runs only if no exception in try
        lines = [ln for ln in text.splitlines() if ln.strip()]
    finally:
        # always runs — cleanup, close resources
        pass
    return parse_key_value(lines)
```

| Clause | When it runs |
|--------|----------------|
| `try` | Protected code |
| `except` | Matching exception raised |
| `else` | No exception in `try` |
| `finally` | Always (even if return/break) |

Catch **specific** exceptions—avoid bare `except:`.

---

## 3. Raising and chaining

```python
if timeout <= 0:
    raise ValueError("timeout must be positive")

try:
    connect()
except ConnectionError as exc:
    raise RuntimeError("deploy aborted") from exc
```

`from exc` preserves the original cause in tracebacks—critical for debugging pipelines.

---

## 4. Custom exceptions (lightweight)

```python
class DeployError(Exception):
    """Base for deploy script failures."""

class HealthCheckError(DeployError):
    def __init__(self, host: str, status: int):
        super().__init__(f"{host} unhealthy HTTP {status}")
        self.host = host
        self.status = status
```

Use sparingly—built-ins cover most I/O cases.

---

## 5. `logging` vs `print`

| `print` | `logging` |
|---------|-----------|
| Always stdout | Levels: DEBUG…CRITICAL |
| No timestamps by default | Timestamps, logger names |
| Hard to filter in CI | Handlers: file, syslog, JSON |

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("deploy")

log.info("starting rollout", extra={})  # use %-formatting or f-strings carefully
log.warning("canary at 50%% error rate")
log.error("rollback triggered")
```

**Library rule:** Libraries log; applications configure handlers. Scripts call `basicConfig` once in `main`.

---

## 6. Logger hierarchy and levels

```python
log = logging.getLogger("handbook.deploy")
child = logging.getLogger("handbook.deploy.canary")

log.setLevel(logging.DEBUG)   # usually set on root/handler instead
```

| Level | Numeric | Typical use |
|-------|---------|-------------|
| DEBUG | 10 | Verbose internals |
| INFO | 20 | Normal progress |
| WARNING | 30 | Recoverable issue |
| ERROR | 40 | Failed step |
| CRITICAL | 50 | Abort entire run |

```bash
PYTHONLOGLEVEL=DEBUG python3 script.py
```

---

## 7. Logging exceptions

```python
try:
    risky()
except Exception:
    log.exception("risky failed")  # includes traceback at ERROR level
    raise
```

---

## 8. Context managers and `with`

Files and locks should use `with`—exceptions still run `finally` cleanup:

```python
with Path("state.json").open() as f:
    data = json.load(f)
# file closed even if json.load raises
```

---

## 9. Lab — Day 6

Work from `python/day6/labs/`.

1. Run `labs/safe_read.py` with missing file, invalid JSON, and valid file.
2. Add a custom `ConfigError` and raise it for empty config.
3. Replace `print` with `logging` in your copy; run at INFO and DEBUG levels.
4. Use `log.exception` in one failure path; confirm traceback in output.
5. Add `finally` that logs "cleanup complete" even on success.
6. Simulate a retry: catch `ConnectionError` (or a local stub), log warning, retry up to 3 times.

**Stretch:** Add a `FileHandler` writing to `deploy.log` alongside StreamHandler.

---

## 10. DevOps connections

- **CI:** Non-zero exit on unhandled exceptions fails the job; log ERROR lines for Splunk/Datadog alerts.
- **Idempotency:** Catch expected "already exists" API errors; re-raise unexpected ones.
- **Secrets:** Never log tokens—catch and redact in `except` blocks.

---

## Quick reference

| Task | Pattern |
|------|---------|
| Catch specific | `except FileNotFoundError:` |
| Re-raise | `raise` |
| Chain | `raise X from e` |
| Log traceback | `log.exception("msg")` |
| Configure | `logging.basicConfig(...)` |
| Logger | `logging.getLogger(__name__)` |

**Next:** [Day 7 — Modules, venv, pip & pyproject.toml](../day7/)
