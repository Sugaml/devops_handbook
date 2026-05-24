#!/usr/bin/env python3
"""Ansible dynamic inventory from JSON host registry."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def load_hosts(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def build_inventory(hosts: list[dict]) -> dict:
    inv: dict = {"_meta": {"hostvars": {}}}
    for entry in hosts:
        host = dict(entry)
        group = host.pop("group", "ungrouped")
        name = host.pop("name")
        inv.setdefault(group, {"hosts": [], "vars": {}})
        inv[group]["hosts"].append(name)
        inv["_meta"]["hostvars"][name] = host
    return inv


def registry_path() -> Path:
    override = os.environ.get("HOST_REGISTRY_PATH")
    if override:
        return Path(override)
    return Path(__file__).parent / "hosts_registry.json"


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        hosts = load_hosts(registry_path())
        print(json.dumps(build_inventory(hosts), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        # Per-host vars already in _meta from --list; Ansible caches them.
        print(json.dumps({}))
    else:
        sys.stderr.write("Usage: dynamic_inventory.py --list | --host <name>\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
