#!/usr/bin/env python3
"""SSH fleet automation lab using Paramiko."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import paramiko
import yaml


def load_inventory(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("hosts", [])


def connect_host(entry: dict) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(
        hostname=entry["host"],
        username=entry.get("user", "ubuntu"),
        key_filename=str(Path(entry.get("key", "~/.ssh/id_ed25519")).expanduser()),
        timeout=int(entry.get("timeout", 10)),
    )
    return client


def run_on_host(entry: dict, command: str) -> dict:
    host = entry["host"]
    try:
        client = connect_host(entry)
    except Exception as exc:
        return {"host": host, "ok": False, "error": str(exc)}
    try:
        _, stdout, stderr = client.exec_command(command, timeout=30)
        code = stdout.channel.recv_exit_status()
        return {
            "host": host,
            "ok": code == 0,
            "exit_code": code,
            "stdout": stdout.read().decode().strip(),
            "stderr": stderr.read().decode().strip(),
        }
    except Exception as exc:
        return {"host": host, "ok": False, "error": str(exc)}
    finally:
        client.close()


def upload_to_host(entry: dict, local: Path, remote: str) -> dict:
    host = entry["host"]
    try:
        client = connect_host(entry)
        sftp = client.open_sftp()
        sftp.put(str(local), remote)
        sftp.close()
        return {"host": host, "ok": True, "uploaded": remote}
    except Exception as exc:
        return {"host": host, "ok": False, "error": str(exc)}
    finally:
        try:
            client.close()
        except Exception:
            pass


def run_fleet(
    hosts: list[dict],
    fn,
    parallel: int,
) -> list[dict]:
    if parallel <= 1 or len(hosts) == 1:
        return [fn(h) for h in hosts]
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = {pool.submit(fn, h): h for h in hosts}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="SSH deploy lab")
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path(__file__).parent / "inventory.yaml",
    )
    parser.add_argument("--parallel", type=int, default=1)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ping", help="Run hostname on all hosts")
    p_exec = sub.add_parser("exec", help="Run arbitrary command")
    p_exec.add_argument("command")
    p_up = sub.add_parser("upload", help="SFTP upload file")
    p_up.add_argument("local", type=Path)
    p_up.add_argument("remote")

    args = parser.parse_args()

    if not args.inventory.exists():
        print(
            f"ERROR: {args.inventory} not found. Copy inventory.yaml.example",
            file=sys.stderr,
        )
        return 1

    hosts = load_inventory(args.inventory)
    if not hosts:
        print("ERROR: no hosts in inventory", file=sys.stderr)
        return 1

    if args.command == "ping":
        results = run_fleet(hosts, lambda h: run_on_host(h, "hostname"), args.parallel)
    elif args.command == "exec":
        results = run_fleet(
            hosts,
            lambda h: run_on_host(h, args.command),
            args.parallel,
        )
    else:
        results = run_fleet(
            hosts,
            lambda h: upload_to_host(h, args.local, args.remote),
            args.parallel,
        )

    failed = sum(1 for r in results if not r.get("ok"))
    print(json.dumps({"results": results, "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
