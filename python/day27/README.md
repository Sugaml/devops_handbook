# Day 27 — asyncio & aiohttp Concurrent Health Checks

**Goal:** Build high-throughput health checkers that probe hundreds of endpoints concurrently using `asyncio` and `aiohttp`, with timeouts, retries, and structured results for incident dashboards.

**Time:** 4–5 hours

**Prerequisites:** Day 26 (structured logging); HTTP basics

---

## 1. Why async for health checks?

Sequential checks against 200 URLs:

```
200 targets × 2s timeout = up to 400 seconds worst case
```

Concurrent async checks with connection pooling:

```
~200 targets in ~2–5 seconds (bounded by concurrency limit)
```

| Sync `requests` loop | asyncio + aiohttp |
|----------------------|-------------------|
| One connection at a time per thread | Thousands of coroutines, few threads |
| Thread pool overhead | Single event loop |
| Simple mental model | Requires async discipline |

Use async when **I/O-bound** (HTTP, DNS, TCP connect). CPU-bound work still belongs in processes.

---

## 2. Core asyncio patterns

```python
import asyncio

async def check_one(url: str) -> bool:
    await asyncio.sleep(0.1)  # simulate I/O
    return True

async def main():
    urls = ["https://a.example", "https://b.example"]
    results = await asyncio.gather(*[check_one(u) for u in urls])
    print(results)

asyncio.run(main())
```

`asyncio.gather` runs coroutines concurrently; use `return_exceptions=True` to avoid one failure cancelling others.

---

## 3. aiohttp session and timeouts

Reuse one `ClientSession` — expensive to create per request:

```python
import aiohttp

timeout = aiohttp.ClientTimeout(total=5, connect=2)
async with aiohttp.ClientSession(timeout=timeout) as session:
    async with session.get(url) as resp:
        body = await resp.text()
        return resp.status, len(body)
```

TLS verification: keep enabled in production; disable only in lab with explicit flag.

---

## 4. Semaphore for bounded concurrency

Unlimited concurrency can overwhelm targets or file descriptors:

```python
sem = asyncio.Semaphore(50)

async def check_with_limit(session, target):
    async with sem:
        return await probe(session, target)
```

Tune `50` based on target capacity and your outbound connection limits.

---

## 5. Retry with exponential backoff

```python
async def probe_with_retry(session, url, attempts=3):
    for attempt in range(attempts):
        try:
            return await probe(session, url)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

Distinguish **retryable** (502, timeout) vs **fatal** (404 on health endpoint) in production checkers.

---

## 6. Structured check results

See `labs/health_checker.py`:

```python
@dataclass
class CheckResult:
    name: str
    url: str
    ok: bool
    status_code: int | None
    latency_ms: float
    error: str | None = None
```

Emit JSON for downstream tools:

```json
{"summary": {"total": 10, "healthy": 9, "unhealthy": 1},
 "results": [{"name": "api", "ok": false, "latency_ms": 5001.2, "error": "timeout"}]}
```

---

## 7. TCP and HTTP health checks

```python
async def tcp_check(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError):
        return False
```

Combine HTTP status checks with TCP for databases and caches.

---

## 8. CLI integration

```bash
python health_checker.py targets.yaml --concurrency 30 --json
python health_checker.py targets.yaml --fail-on-error   # exit 1 if any unhealthy
```

Exit codes enable CI smoke tests and pre-deploy gates.

---

## 9. Lab — Day 27

Work from `python/day27/labs/`.

1. Install: `pip install aiohttp pyyaml`.
2. Run `python health_checker.py targets.yaml` — human-readable summary.
3. Run with `--json` and pipe to `jq '.summary'`.
4. Add a bad URL to `targets.yaml`; confirm `--fail-on-error` exits 1.
5. Lower concurrency to 2 with `--concurrency 2` and compare timing.
6. Run against public endpoints (e.g. `https://httpbin.org/status/200`) to verify real HTTP.
7. **Stretch:** Add `--watch 30` to re-run checks every 30 seconds until Ctrl+C.

**Success criteria:** All targets checked concurrently; JSON output includes latency; exit code reflects fleet health.

---

## 10. DevOps connections

- **Load balancer validation:** After Terraform apply, async checker verifies all backends before DNS cutover.
- **Incident response:** Day 30 toolkit embeds this module for rapid fleet assessment.
- **Synthetic monitoring:** CronJob runs checker every minute; Prometheus pushgateway or JSON logs feed alerts.

---

## Quick reference

| Task | Command |
|------|---------|
| Run checks | `python health_checker.py targets.yaml` |
| JSON output | `python health_checker.py targets.yaml --json` |
| Limit concurrency | `--concurrency 50` |
| CI gate | `--fail-on-error` |
| Timeout | `--timeout 5` |

**Next:** [Day 28 — Packaging with Poetry](../day28/)
