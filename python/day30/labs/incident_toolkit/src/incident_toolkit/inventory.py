"""Host registry and inventory helpers."""
from __future__ import annotations

import json
from pathlib import Path

from incident_toolkit.config import settings
from incident_toolkit.models import HostRecord, InventoryGroup


def load_hosts(path: Path | None = None) -> list[HostRecord]:
    registry = path or settings.hosts_registry
    raw = json.loads(registry.read_text())
    return [HostRecord.model_validate(item) for item in raw]


def build_inventory_groups(hosts: list[HostRecord]) -> list[InventoryGroup]:
    groups: dict[str, list[HostRecord]] = {}
    for host in hosts:
        groups.setdefault(host.group, []).append(host)
    return [InventoryGroup(name=name, hosts=members) for name, members in sorted(groups.items())]


def to_ansible_inventory(hosts: list[HostRecord]) -> dict:
    inv: dict = {"_meta": {"hostvars": {}}}
    for host in hosts:
        inv.setdefault(host.group, {"hosts": []})
        inv[host.group]["hosts"].append(host.name)
        inv["_meta"]["hostvars"][host.name] = {
            "ansible_host": host.ansible_host,
            "env": host.env,
        }
    return inv
