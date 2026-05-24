#!/usr/bin/env python3
"""Concurrent HTTP/TCP health checker using asyncio and aiohttp."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import aiohttp
import yaml


@dataclass
class CheckResult:
    name: str
    url: str
    ok: bool
    status_code: int | None
    latency_ms: float
    error: str | None = None


async def http_probe(
    session: aiohttp.ClientSession,
    name: str,
    url: str,
    *,
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
    except Exception as exc:  # noqa: BLE001 — aggregate for reporting
        latency = (time.perf_counter() - start) * 1000
        return CheckResult(
            name=name,
            url=url,
            ok=False,
            status_code=None,
            latency_ms=round(latency, 2),
            error=str(exc),
        )


async def run_checks(
    targets: list[dict[str, Any]],
    *,
    concurrency: int,
    timeout: float,
) -> list[CheckResult]:
    sem = asyncio.Semaphore(concurrency)
    client_timeout = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        async def bounded(target: dict[str, Any]) -> CheckResult:
            async with sem:
                return await http_probe(
                    session,
                    target["name"],
                    target["url"],
                    expected_status=target.get("expected_status", 200),
                )

        return list(await asyncio.gather(*[bounded(t) for t in targets]))


def load_targets(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text())
    return data.get("targets", [])


def summarize(results: list[CheckResult]) -> dict[str, int]:
    healthy = sum(1 for r in results if r.ok)
    return {"total": len(results), "healthy": healthy, "unhealthy": len(results) - healthy}


def print_human(results: list[CheckResult]) -> None:
    summary = summarize(results)
    print(f"Checked {summary['total']} targets: {summary['healthy']} healthy, {summary['unhealthy']} unhealthy")
    for result in results:
        status = "OK" if result.ok else "FAIL"
        detail = result.error or f"HTTP {result.status_code}"
        print(f"  [{status}] {result.name} ({result.latency_ms}ms) — {detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Concurrent health checker")
    parser.add_argument("targets", type=Path, help="YAML file with targets list")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    targets = load_targets(args.targets)
    if not targets:
        print("No targets defined", file=sys.stderr)
        sys.exit(2)

    results = asyncio.run(
        run_checks(targets, concurrency=args.concurrency, timeout=args.timeout)
    )

    if args.json_output:
        payload = {"summary": summarize(results), "results": [asdict(r) for r in results]}
        print(json.dumps(payload, indent=2))
    else:
        print_human(results)

    if args.fail_on_error and any(not r.ok for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
