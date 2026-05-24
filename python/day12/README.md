# Day 12 — HTTP with requests & httpx: API Health Checks

**Goal:** Build production-style HTTP health check scripts using `requests` and `httpx`, with timeouts, retries, status validation, and structured reporting for CI and on-call use.

**Time:** 4–5 hours (theory + hands-on)

---

## 1. Why HTTP health checks in DevOps

Load balancers probe endpoints; your Python scripts do the same **before** and **after** deploys:

```
  deploy script
       │
       ├── POST /deploy
       │
       └── poll GET /health until 200 (or timeout)
```

| Consumer | What it needs |
|----------|---------------|
| CI pipeline | Exit code 0/1, JSON summary |
| Cron / systemd timer | Log failures, alert on-call |
| Pre-flight gate | Check 10+ services in parallel |

**requests** is the battle-tested sync library. **httpx** adds HTTP/2, async, and a similar API — ideal for checking many endpoints concurrently.

---

## 2. Install and basic GET

```bash
pip install requests httpx
```

```python
import requests

resp = requests.get(
    "https://httpbin.org/status/200",
    timeout=(3.05, 10),  # (connect, read) seconds
)
resp.raise_for_status()
print(resp.status_code, resp.elapsed.total_seconds())
```

**Always set timeouts.** A hung connection blocks deploy pipelines indefinitely.

---

## 3. Health check contract

Define what "healthy" means beyond HTTP 200:

```python
def is_healthy(resp: requests.Response) -> tuple[bool, str]:
    if resp.status_code != 200:
        return False, f"status {resp.status_code}"
    try:
        body = resp.json()
    except ValueError:
        return False, "response is not JSON"
    if body.get("status") != "ok":
        return False, f"body status={body.get('status')!r}"
    return True, "ok"
```

Common patterns:

| Endpoint | Expected |
|----------|----------|
| `/health` | `200`, optional JSON `{"status":"ok"}` |
| `/ready` | `200` only when dependencies are up |
| `/metrics` | `200`, Prometheus text format |

---

## 4. Retries with exponential backoff

Transient failures happen during rolling deploys. Use `urllib3.util.retry` via requests adapters:

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def session_with_retries(total: int = 3, backoff: float = 0.5) -> requests.Session:
    retry = Retry(
        total=total,
        backoff_factor=backoff,
        status_forcelist=(502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    sess = requests.Session()
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    return sess
```

For custom retry loops (poll until ready):

```python
import time

def wait_until_healthy(url: str, timeout: int = 120, interval: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    sess = session_with_retries()
    while time.monotonic() < deadline:
        try:
            resp = sess.get(url, timeout=10)
            ok, _ = is_healthy(resp)
            if ok:
                return True
        except requests.RequestException:
            pass
        time.sleep(interval)
    return False
```

---

## 5. httpx: async parallel checks

When checking dozens of services, async reduces wall-clock time:

```python
import asyncio
import httpx

async def check_one(client: httpx.AsyncClient, name: str, url: str) -> dict:
    try:
        resp = await client.get(url, timeout=10.0)
        ok = resp.status_code == 200
        return {"name": name, "ok": ok, "status": resp.status_code}
    except httpx.HTTPError as exc:
        return {"name": name, "ok": False, "error": str(exc)}

async def check_all(endpoints: list[tuple[str, str]]) -> list[dict]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [check_one(client, name, url) for name, url in endpoints]
        return await asyncio.gather(*tasks)
```

Run with `asyncio.run(check_all(...))`.

---

## 6. TLS, auth, and headers

```python
# Bearer token (internal API)
headers = {"Authorization": f"Bearer {token}"}
resp = requests.get(url, headers=headers, timeout=10)

# mTLS (client cert)
resp = requests.get(url, cert=("/path/client.crt", "/path/client.key"), timeout=10)

# Skip verify — lab only; never in production without pinning
resp = requests.get(url, verify=False)  # noqa: S501
```

Store tokens in environment variables (Day 13), never in source code.

---

## 7. Structured output for CI

```python
import json
import sys

summary = {"passed": 2, "failed": 1, "results": [...]}
print(json.dumps(summary, indent=2))
sys.exit(0 if summary["failed"] == 0 else 1)
```

GitHub Actions, GitLab CI, and Jenkins all key off process exit codes. JSON stdout enables downstream parsing.

---

## 8. Mock server for local labs

```bash
# Terminal 1 — simple health endpoint
python3 -m http.server 8765

# Terminal 2 — or use httpbin locally via Docker
docker run --rm -p 8080:80 kennethreitz/httpbin
curl -s http://localhost:8080/status/200
```

The lab script reads endpoints from YAML so you can point at httpbin or a local mock.

---

## 9. Lab — Day 12

Work from `python/day12/labs/`.

1. `pip install requests httpx pyyaml`.
2. Run `python health_check.py --config endpoints.yaml` against default httpbin URLs.
3. Change one URL to `/status/503` in `endpoints.yaml`; confirm exit code 1 and JSON report shows failure.
4. Run with `--async` flag to use httpx parallel mode; compare elapsed time with 5+ endpoints.
5. Add `--wait https://httpbin.org/delay/3` — script polls until success or `--timeout` seconds.
6. Run with `--retries 5` during a simulated deploy (toggle httpbin status with `/status/200` vs `/status/503`).

**Stretch:** Emit JUnit XML for CI test report ingestion.

---

## 10. DevOps connections

- **Kubernetes probes:** Liveness/readiness mirror what you automate externally — keep paths consistent.
- **Load balancers:** ALB/NLB target health uses similar HTTP/TCP checks; your script validates before registering targets.
- **Synthetic monitoring:** Datadog/Pingdom do this 24/7; Day 12 teaches the same logic you embed in deploy scripts.

---

## Quick reference

| Task | Code |
|------|------|
| GET with timeout | `requests.get(url, timeout=10)` |
| Raise on 4xx/5xx | `resp.raise_for_status()` |
| Retry 502/503 | `HTTPAdapter` + `Retry` |
| Parallel async | `httpx.AsyncClient` + `asyncio.gather` |
| CI exit code | `sys.exit(1 if failures else 0)` |

**Next:** [Day 13 — Environment variables & secrets hygiene](../day13/)
