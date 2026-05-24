# Day 9 — subprocess: Running Shell Commands Safely

**Goal:** Invoke external tools (`git`, `kubectl`, `terraform`, `ssh`) from Python without shell injection; capture output; handle timeouts and exit codes.

**Time:** 4–5 hours

---

## 1. Prefer argv lists over shell strings

```python
import subprocess

# SAFE — no shell interpretation
subprocess.run(
    ["git", "rev-parse", "HEAD"],
    check=True,
    text=True,
    capture_output=True,
)

# DANGEROUS if branch contains metacharacters
# subprocess.run(f"git checkout {branch}", shell=True)
```

**Rule:** `shell=True` only when you need shell features—and never with untrusted input.

---

## 2. `subprocess.run` essentials

```python
result = subprocess.run(
    ["kubectl", "get", "pods", "-n", "handbook-lab", "-o", "json"],
    capture_output=True,
    text=True,
    timeout=60,
)

print(result.returncode)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
```

| Flag | Effect |
|------|--------|
| `check=True` | Raise `CalledProcessError` if exit != 0 |
| `capture_output=True` | Pipe stdout/stderr |
| `text=True` | Decode as str (UTF-8) |
| `timeout=N` | Kill if hung |
| `cwd="/path"` | Working directory |
| `env={**os.environ, "KUBECONFIG": "..."}` | Environment |

---

## 3. Handling failures

```python
try:
    subprocess.run(["terraform", "plan"], check=True, text=True)
except subprocess.CalledProcessError as exc:
    print(f"terraform failed code={exc.returncode}")
    print(exc.stdout)
    print(exc.stderr)
except subprocess.TimeoutExpired:
    print("terraform plan timed out")
```

---

## 4. Streaming output (long-running commands)

For live logs, don't capture—inherit or stream line by line:

```python
proc = subprocess.Popen(
    ["ansible-playbook", "site.yml"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

assert proc.stdout is not None
for line in proc.stdout:
    print(line, end="")

code = proc.wait()
```

Or inherit terminal:

```python
subprocess.run(["docker", "compose", "up"], check=False)
```

---

## 5. `subprocess.list2cmdline` for debugging

```python
import shlex
cmd = ["ssh", "user@host", "systemctl", "status", "nginx"]
print(shlex.join(cmd))   # Python 3.12+
```

Operators can copy-paste logged commands.

---

## 6. Security checklist

| Risk | Mitigation |
|------|------------|
| Shell injection | Use list argv, `shell=False` |
| Secrets in argv | Visible in `ps`—use env or files |
| Secrets in logs | Redact before `print(result)` |
| Hung processes | Always set `timeout` in CI |
| Huge output | Stream or write to temp file |

---

## 7. Wrapping common ops tools

```python
def kubectl(*args: str) -> str:
    cmd = ["kubectl", *args]
    result = subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=True,
        timeout=120,
    )
    return result.stdout
```

Centralize wrappers so timeouts and logging stay consistent.

---

## 8. Lab — Day 9

Work from `python/day9/labs/`.

1. Run `run_remote_cmd.py --dry-run` and inspect printed argv.
2. Run with `echo hello` as the remote command (local simulation)—capture stdout.
3. Force failure: exit code non-zero; catch `CalledProcessError`.
4. Add `--timeout` flag; run `sleep 10` with timeout 1 and handle `TimeoutExpired`.
5. Log full command with `shlex.join` before execution.
6. Refactor to refuse `shell=True` paths—grep your script for safety.

**Stretch:** Stream output from `git log --oneline -n 20` line by line.

---

## 9. DevOps connections

- **Orchestration:** Python coordinates Terraform → Ansible → smoke test; each step is a subprocess.
- **CI agents:** Same patterns as Jenkins `sh` steps but with structured error handling.
- **Windows:** Use `shell=False` with full paths to `.exe`; consider `msvcrt` separately (out of scope here).

---

## Quick reference

| Task | API |
|------|-----|
| Run and wait | `subprocess.run([...], check=True)` |
| Capture | `capture_output=True, text=True` |
| Timeout | `timeout=60` |
| Stream | `Popen` + iterate stdout |
| Avoid shell | `shell=False` (default) |

**Next:** [Day 10 — os, sys, pathlib, permissions & glob](../day10/)
