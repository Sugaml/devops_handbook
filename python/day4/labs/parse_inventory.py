#!/usr/bin/env python3
"""Parse inline inventory and emit JSON — Day 4 lab."""

import json

INVENTORY_TEXT = """
# hostname, ip, role
web1, 10.0.0.11, web
web2, 10.0.0.12, web
db1, 10.0.0.21, db
api1, 10.0.0.31, api
"""


def parse_inventory(text: str) -> list[dict[str, str]]:
    hosts: list[dict[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            continue
        name, ip, role = parts
        hosts.append({"name": name, "ip": ip, "role": role})
    return hosts


def main() -> None:
    hosts = parse_inventory(INVENTORY_TEXT)
    web_only = [h for h in hosts if h["role"] == "web"]
    name_to_ip = {h["name"]: h["ip"] for h in hosts}
    print(json.dumps({"all": hosts, "web": web_only, "name_to_ip": name_to_ip}, indent=2))


if __name__ == "__main__":
    main()
