# Day 3 — Functions, Docstrings, Scope, *args/**kwargs

**Goal:** Structure ops scripts with reusable functions, document them, understand scope, and accept flexible parameters for wrappers around tools and APIs.

**Time:** 4–5 hours

---

## 1. Defining and calling functions

```python
def health_check(url: str, timeout: float = 5.0) -> bool:
  """Return True if URL responds with HTTP < 400."""
  # implementation omitted in handbook
  return True

ok = health_check("https://api.example.com/healthz")
```

| Part | Role |
|------|------|
| Parameters | Inputs with optional defaults |
| Return type hint | Documents what callers get |
| `return` | Sends value back; bare `return` → `None` |

---

## 2. Docstrings — document for operators

Use triple-quoted strings immediately after `def`:

```python
def rotate_secret(service: str, dry_run: bool = True) -> str:
    """
    Rotate credentials for a service in Vault.

    Args:
        service: Logical name (e.g. 'payments-api').
        dry_run: If True, print plan only.

    Returns:
        New secret version id.

    Raises:
        ValueError: Unknown service name.
    """
```

Access in REPL: `help(rotate_secret)` or `rotate_secret.__doc__`.

**Style:** Google or NumPy docstring layout; be consistent within a repo.

---

## 3. Scope: LEGB rule

Python resolves names in order: **L**ocal → **E**nclosing → **G**lobal → **B**uilt-in.

```python
REGION = "us-east-1"   # module global

def deploy(region: str) -> None:
    print(region)      # local parameter shadows global

def show_default() -> None:
    print(REGION)      # global
```

Modify global (rare—prefer passing args):

```python
call_count = 0

def inc() -> None:
    global call_count
    call_count += 1
```

**Best practice:** Avoid `global`; return values or use a small class/dataclass for state.

---

## 4. Default arguments — mutable trap

Never use mutable defaults:

```python
# BAD
def add_host(host: str, fleet: list = []) -> list:
    fleet.append(host)
    return fleet

# GOOD
def add_host(host: str, fleet: list | None = None) -> list:
    if fleet is None:
        fleet = []
    fleet.append(host)
    return fleet
```

---

## 5. `*args` — variable positional arguments

```python
def run_checks(*checks: str) -> None:
    for name in checks:
        print(f"running {name}")

run_checks("disk", "memory", "tls")
```

Unpack when calling:

```python
suite = ["dns", "http", "tcp"]
run_checks(*suite)
```

---

## 6. `**kwargs` — variable keyword arguments

```python
def tag_resource(resource_id: str, **tags: str) -> dict:
    return {"id": resource_id, "tags": tags}

tag_resource("i-0abc", env="prod", team="platform")
```

Combine with explicit parameters:

```python
def connect(host: str, port: int = 22, **ssh_options: str) -> None:
    print(host, port, ssh_options)
```

---

## 7. Unpacking in function signatures

```python
def notify(message: str, *channels: str, priority: str = "normal") -> None:
    """
    *channels: positional-only after first arg
    priority: keyword-only (must pass priority=...)
    """
```

Python 3.8+ positional-only with `/`:

```python
def exec_command(cmd: str, /, timeout: int = 30) -> int:
    ...
```

---

## 8. First-class functions and lambdas

Functions are objects—pass them like callbacks:

```python
def retry(fn, attempts: int = 3):
    for _ in range(attempts):
        try:
            return fn()
        except OSError:
            pass
    raise RuntimeError("exhausted retries")
```

Lambdas for tiny one-liners (don't abuse):

```python
hosts.sort(key=lambda h: h["name"])
```

---

## 9. Lab — Day 3

Work from `python/day3/labs/`.

1. Read `deploy_helpers.py`; run it and trace which scope each variable uses.
2. Add a function `format_release(app: str, version: str, env: str) -> str` with a full docstring.
3. Implement `build_ssh_command(host: str, *extra_args: str, user: str = "deploy") -> list[str]` returning argv list.
4. Refactor duplicate print logic into `log_step(step: str, **context: str)`.
5. Fix a deliberate mutable-default bug if you introduce one in your extensions.
6. Call `build_ssh_command` with unpacked list: `extra = ["-o", "StrictHostKeyChecking=no"]`.

**Stretch:** Add keyword-only `dry_run: bool = False` to a deploy function; callers must use `dry_run=True`.

---

## 10. DevOps connections

- **Thin wrappers:** `*args/**kwargs` mirror CLI flags passed through to `kubectl`, `aws`, `terraform`.
- **Testability:** Small pure functions (parse inventory, build URL) unit-test easily in CI.
- **Libraries:** Shared `handbook_utils` modules start as functions on Day 3, packages on Day 7.

---

## Quick reference

| Task | Syntax |
|------|--------|
| Define | `def f(x: int) -> str:` |
| Default | `def f(x, timeout=5):` |
| Var pos | `*args` |
| Var kw | `**kwargs` |
| Unpack call | `f(*a, **kw)` |
| Docstring | `"""..."""` under `def` |

**Next:** [Day 4 — Lists, dicts, sets & comprehensions](../day4/)
