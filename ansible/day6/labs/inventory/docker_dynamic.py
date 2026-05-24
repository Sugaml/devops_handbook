#!/usr/bin/env python3
"""Legacy-style dynamic inventory example — prefer inventory/docker.yml plugin in production."""
from __future__ import annotations

import json
import subprocess


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True)


def container_ssh_port(name: str) -> int | None:
    try:
        out = run([
            "docker", "port", name, "22/tcp",
        ]).strip()
        # 0.0.0.0:2221
        return int(out.split(":")[-1])
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return None


def build_inventory() -> dict:
    ids = run(["docker", "ps", "-q", "--filter", "label=handbook=day6"]).split()
    hosts: dict = {}
    for cid in ids:
        if not cid:
            continue
        name = run(["docker", "inspect", "--format", "{{.Name}}", cid]).lstrip("/")
        port = container_ssh_port(name)
        if port is None:
            continue
        hosts[name] = {
            "ansible_host": "127.0.0.1",
            "ansible_port": port,
            "ansible_user": "ansible",
            "ansible_python_interpreter": "/usr/bin/python3",
        }

    return {
        "_meta": {"hostvars": hosts},
        "all": {"hosts": list(hosts.keys())},
        "webservers": {"hosts": [h for h in hosts if h.startswith("handbook-web")]},
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        print(json.dumps(build_inventory(), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        print(json.dumps({}))
    else:
        sys.stderr.write("usage: docker_dynamic.py --list | --host <name>\n")
        sys.exit(1)
