#!/usr/bin/env python3
"""HTTP health checker — sync (requests) and async (httpx) modes."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def load_endpoints(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("endpoints", [])


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


def evaluate_response(resp: requests.Response, expect_json_status: str | None) -> tuple[bool, str]:
    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}"
    if expect_json_status:
        try:
            body = resp.json()
        except ValueError:
            return False, "invalid JSON body"
        if body.get("status") != expect_json_status:
            return False, f"body status={body.get('status')!r}"
    return True, "ok"


def check_sync(endpoint: dict[str, Any], retries: int) -> dict[str, Any]:
    name = endpoint["name"]
    url = endpoint["url"]
    expect = endpoint.get("expect_json_status")
    sess = session_with_retries(total=retries)
    started = time.monotonic()
    try:
        resp = sess.get(url, timeout=(3.05, 15))
        ok, detail = evaluate_response(resp, expect)
        return {
            "name": name,
            "url": url,
            "ok": ok,
            "detail": detail,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }
    except requests.RequestException as exc:
        return {
            "name": name,
            "url": url,
            "ok": False,
            "detail": str(exc),
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }


async def check_async(endpoint: dict[str, Any]) -> dict[str, Any]:
    name = endpoint["name"]
    url = endpoint["url"]
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url)
        ok = resp.status_code == 200
        detail = "ok" if ok else f"HTTP {resp.status_code}"
        return {
            "name": name,
            "url": url,
            "ok": ok,
            "detail": detail,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }
    except httpx.HTTPError as exc:
        return {
            "name": name,
            "url": url,
            "ok": False,
            "detail": str(exc),
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }


async def check_all_async(endpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return await asyncio.gather(*[check_async(ep) for ep in endpoints])


def wait_until(url: str, timeout: int, interval: float, retries: int) -> bool:
    deadline = time.monotonic() + timeout
    sess = session_with_retries(total=retries)
    while time.monotonic() < deadline:
        try:
            resp = sess.get(url, timeout=15)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(interval)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="API health check lab")
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "endpoints.yaml")
    parser.add_argument("--async", dest="use_async", action="store_true", help="Use httpx async")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--wait", metavar="URL", help="Poll URL until 200 or timeout")
    parser.add_argument("--timeout", type=int, default=60, help="Wait timeout seconds")
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()

    if args.wait:
        ok = wait_until(args.wait, args.timeout, args.interval, args.retries)
        print(json.dumps({"wait_url": args.wait, "ok": ok}))
        return 0 if ok else 1

    endpoints = load_endpoints(args.config)
    if args.use_async:
        results = asyncio.run(check_all_async(endpoints))
    else:
        results = [check_sync(ep, args.retries) for ep in endpoints]

    failed = sum(1 for r in results if not r["ok"])
    summary = {"passed": len(results) - failed, "failed": failed, "results": results}
    print(json.dumps(summary, indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
