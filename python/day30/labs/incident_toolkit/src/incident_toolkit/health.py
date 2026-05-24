"""Async concurrent health checks."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import aiohttp
import yaml

from incident_toolkit.metrics import CHECK_DURATION
from incident_toolkit.models import AssessResult, CheckResult, HealthSummary, IncidentContext


def load_targets(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text())
    return list(data.get("targets", []))


async def probe(
    session: aiohttp.ClientSession,
    name: str,
    url: str,
    expected_status: int = 200,
) -> CheckResult:
    start = time.perf_counter()
    try:
        async with session.get(url) as resp:
            await resp.read()
            latency = (time.perf_counter() - start) * 1000
            ok = resp.status == expected_status
            return CheckResult(
                name=name,
                url=url,
                ok=ok,
                status_code=resp.status,
                latency_ms=round(latency, 2),
                error=None if ok else f"expected {expected_status}, got {resp.status}",
            )
    except Exception as exc:  # noqa: BLE001
        latency = (time.perf_counter() - start) * 1000
        return CheckResult(
            name=name,
            url=url,
            ok=False,
            latency_ms=round(latency, 2),
            error=str(exc),
        )


async def run_checks(
    targets: list[dict[str, Any]],
    *,
    concurrency: int = 30,
    timeout: float = 5.0,
) -> list[CheckResult]:
    import asyncio

    sem = asyncio.Semaphore(concurrency)
    client_timeout = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        async def bounded(target: dict[str, Any]) -> CheckResult:
            async with sem:
                return await probe(
                    session,
                    target["name"],
                    target["url"],
                    expected_status=target.get("expected_status", 200),
                )

        with CHECK_DURATION.time():
            return list(await asyncio.gather(*[bounded(t) for t in targets]))


def summarize(results: list[CheckResult]) -> HealthSummary:
    healthy = sum(1 for r in results if r.ok)
    return HealthSummary(total=len(results), healthy=healthy, unhealthy=len(results) - healthy)


async def assess(
    targets_path: Path,
    ctx: IncidentContext,
    *,
    concurrency: int = 30,
) -> AssessResult:
    targets = load_targets(targets_path)
    results = await run_checks(targets, concurrency=concurrency)
    return AssessResult(
        incident_id=ctx.incident_id,
        environment=ctx.environment,
        summary=summarize(results),
        results=results,
    )
