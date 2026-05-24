#!/usr/bin/env python3
"""Docker automation lab — SDK and subprocess patterns."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

try:
    import docker
    import docker.errors
except ImportError:
    print("ERROR: pip install docker", file=sys.stderr)
    raise


def cmd_ps(client: docker.DockerClient) -> int:
    rows = []
    for c in client.containers.list(all=True):
        rows.append(
            {
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags or [c.image.short_id],
            }
        )
    print(json.dumps({"containers": rows}, indent=2))
    return 0


def cmd_ps_subprocess() -> int:
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{json .}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return result.returncode
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    rows = [json.loads(ln) for ln in lines]
    print(json.dumps({"containers": rows}, indent=2))
    return 0


def cmd_run_alpine(client: docker.DockerClient) -> int:
    out = client.containers.run(
        "alpine:3.19",
        command=["echo", "handbook-day16"],
        remove=True,
        stdout=True,
        stderr=True,
    )
    print(json.dumps({"output": out.decode().strip()}, indent=2))
    return 0


def cmd_inspect(client: docker.DockerClient, name: str) -> int:
    try:
        c = client.containers.get(name)
    except docker.errors.NotFound:
        print(f"ERROR: container {name!r} not found", file=sys.stderr)
        return 1
    state = c.attrs["State"]
    ports = c.attrs.get("NetworkSettings", {}).get("Ports", {})
    health = state.get("Health", {}).get("Status")
    print(
        json.dumps(
            {
                "name": c.name,
                "status": c.status,
                "health": health,
                "started_at": state.get("StartedAt"),
                "ports": ports,
            },
            indent=2,
        )
    )
    return 0


def cmd_rm(client: docker.DockerClient, name: str) -> int:
    try:
        c = client.containers.get(name)
    except docker.errors.NotFound:
        print(f"ERROR: container {name!r} not found", file=sys.stderr)
        return 1
    c.stop(timeout=10)
    c.remove()
    print(json.dumps({"removed": name}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Docker ops lab")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ps", help="List containers via SDK")
    sub.add_parser("ps-subprocess", help="List containers via docker CLI")
    sub.add_parser("run-alpine", help="One-off alpine echo")
    p_insp = sub.add_parser("inspect", help="Inspect container")
    p_insp.add_argument("name")
    p_rm = sub.add_parser("rm", help="Stop and remove container")
    p_rm.add_argument("name")
    args = parser.parse_args()

    if args.command == "ps-subprocess":
        return cmd_ps_subprocess()

    try:
        client = docker.from_env()
        client.ping()
    except docker.errors.DockerException as exc:
        print(f"ERROR: Docker not available: {exc}", file=sys.stderr)
        return 1

    handlers = {
        "ps": lambda: cmd_ps(client),
        "run-alpine": lambda: cmd_run_alpine(client),
        "inspect": lambda: cmd_inspect(client, args.name),
        "rm": lambda: cmd_rm(client, args.name),
    }
    return handlers[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
