# Day 21 — Ansible Programmatic Use & Dynamic Inventory

**Goal:** Drive Ansible from Python for CI pipelines, generate dynamic inventory from cloud APIs or databases, and integrate playbook runs into automation workflows.

**Time:** 4–5 hours

**Prerequisites:** Ansible installed on control node; SSH access to at least one lab host (see [ansible/day1](../../ansible/day1/))

---

## 1. Why call Ansible from Python?

| Shell one-liner | Python orchestration |
|-----------------|----------------------|
| Hard to parse JSON results | Structured `PlaybookExecutor` output |
| No retry/backoff logic | Integrate with your error handling |
| Secrets in process list | Load from vault/env in code |
| Static inventory files | Generate inventory at runtime |

DevOps use cases:

- Post-Terraform hook: configure freshly created VMs before marking them ready
- Nightly drift remediation triggered by Airflow/Dagster
- Self-service portal that runs approved playbooks with validated parameters
- Dynamic inventory from AWS EC2, Azure VMSS, or Kubernetes node labels

---

## 2. Dynamic inventory contract

Ansible expects inventory plugins or executable scripts that print JSON:

```json
{
  "_meta": { "hostvars": {} },
  "webservers": {
    "hosts": ["web1", "web2"],
    "vars": { "ansible_user": "ubuntu" }
  },
  "dbservers": {
    "hosts": ["db1"]
  }
}
```

Executable inventory:

```bash
chmod +x inventory/ec2_dynamic.py
ansible-inventory -i inventory/ec2_dynamic.py --graph
```

Or configure in `ansible.cfg`:

```ini
[defaults]
inventory = inventory/ec2_dynamic.py,inventory/static.yml
enable_plugins = host_list, script, yaml, ini
```

**Rule:** Dynamic scripts must be fast (<10s), idempotent, and cacheable for large fleets.

---

## 3. Building inventory from a data source

See `labs/dynamic_inventory.py` — reads host metadata from JSON and emits Ansible inventory.

```python
#!/usr/bin/env python3
"""Ansible dynamic inventory from JSON host registry."""
import json
import sys
from pathlib import Path

def build_inventory(hosts: list[dict]) -> dict:
    inv = {"_meta": {"hostvars": {}}}
    for host in hosts:
        group = host.pop("group", "ungrouped")
        name = host["name"]
        inv.setdefault(group, {"hosts": [], "vars": {}})
        inv[group]["hosts"].append(name)
        inv["_meta"]["hostvars"][name] = host
    return inv

def main() -> None:
    data_path = Path(__file__).parent / "hosts_registry.json"
    hosts = json.loads(data_path.read_text())
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        print(json.dumps(build_inventory(hosts), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        print(json.dumps({}))
    else:
        sys.stderr.write("Usage: dynamic_inventory.py --list | --host <name>\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

Test locally:

```bash
cd python/day21/labs
python3 dynamic_inventory.py --list | jq .
ansible-inventory -i dynamic_inventory.py --graph
```

---

## 4. Cloud-backed inventory (EC2 pattern)

Production teams often wrap boto3:

```python
import boto3

def ec2_inventory(region: str, tag_filter: dict) -> dict:
    ec2 = boto3.client("ec2", region_name=region)
    filters = [{"Name": f"tag:{k}", "Values": [v]} for k, v in tag_filter.items()]
    filters.append({"Name": "instance-state-name", "Values": ["running"]})
    resp = ec2.describe_instances(Filters=filters)
    inv = {"_meta": {"hostvars": {}}}
    for reservation in resp["Reservations"]:
        for inst in reservation["Instances"]:
            name = next(
                (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                inst["InstanceId"],
            )
            group = next(
                (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "ansible_group"),
                "ungrouped",
            )
            inv.setdefault(group, {"hosts": []})
            inv[group]["hosts"].append(name)
            inv["_meta"]["hostvars"][name] = {
                "ansible_host": inst.get("PrivateIpAddress"),
                "ansible_user": "ubuntu",
                "instance_id": inst["InstanceId"],
            }
    return inv
```

**Security:** Use IAM role on the runner — never embed long-lived keys in inventory scripts.

---

## 5. Running playbooks from Python

### Option A — `ansible-runner` (recommended)

```bash
pip install ansible-runner
```

```python
import ansible_runner

result = ansible_runner.run(
    playbook="playbooks/ping.yml",
    inventory="dynamic_inventory.py",
    extravars={"target_env": "staging"},
    quiet=False,
)

if result.status != "successful":
    raise RuntimeError(f"Playbook failed: {result.rc}")
for event in result.events:
  if event["event"] == "runner_on_failed":
      print(event["event_data"]["res"])
```

### Option B — `subprocess` with `ansible-playbook`

Use when runner is unavailable; parse `-json` output or rely on exit codes:

```python
import subprocess

def run_playbook(playbook: str, inventory: str, limit: str | None = None) -> int:
    cmd = ["ansible-playbook", playbook, "-i", inventory]
    if limit:
        cmd.extend(["--limit", limit])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout)
    if proc.returncode:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode
```

See `labs/run_playbook.py` for a complete wrapper with logging and `--check` support.

---

## 6. Parsing results for CI gates

Fail the pipeline if any host reports `failed` or unexpected `changed`:

```python
def summarize_runner_result(result) -> dict:
    stats = result.stats
    return {
        "ok": sum(h.get("ok", 0) for h in stats.values()),
        "changed": sum(h.get("changed", 0) for h in stats.values()),
        "failed": sum(h.get("failures", 0) for h in stats.values()),
        "unreachable": sum(h.get("unreachable", 0) for h in stats.values()),
    }
```

In GitHub Actions, emit these counts as step outputs for Slack notifications.

---

## 7. Inventory caching

For 500+ hosts, cache inventory to avoid API throttling:

```python
import json
import time
from pathlib import Path

CACHE_TTL = 300
CACHE_FILE = Path("/tmp/ansible-inv-cache.json")

def cached_inventory(fetch_fn):
    if CACHE_FILE.exists() and time.time() - CACHE_FILE.stat().st_mtime < CACHE_TTL:
        return json.loads(CACHE_FILE.read_text())
    inv = fetch_fn()
    CACHE_FILE.write_text(json.dumps(inv))
    return inv
```

Invalidate cache on deploy events or pass `--refresh-inventory` from your CLI.

---

## 8. Lab — Day 21

Work from `python/day21/labs/`.

1. Review `hosts_registry.json` — add a host in group `webservers` with your lab IP as `ansible_host`.
2. Run `python3 dynamic_inventory.py --list` and confirm groups match the registry.
3. Run `ansible-inventory -i dynamic_inventory.py --graph`.
4. Execute `python3 run_playbook.py --playbook playbooks/ping.yml --check` against your inventory.
5. Remove `--check` and confirm all hosts return `pong`.
6. Modify `run_playbook.py` to accept `--extra-var key=value` and pass `target_env=handbook`.
7. **Stretch:** Extend `dynamic_inventory.py` to read from an environment variable `HOST_REGISTRY_URL` (mock with a local file path).

**Success criteria:** Dynamic inventory lists your hosts; Python wrapper runs ping playbook with exit code 0.

---

## 9. DevOps connections

- **Terraform → Ansible:** Use `terraform output -json` as input to your inventory builder instead of duplicating IP lists.
- **AWX / Ansible Automation Platform:** Wraps the same concepts with RBAC and job templates — your Python code becomes custom credential/inventory plugins.
- **GitOps:** Prefer declarative config in git; use dynamic inventory only for ephemeral resources (spot instances, autoscaling groups).

---

## Quick reference

| Task | Command |
|------|---------|
| Test dynamic inventory | `ansible-inventory -i script.py --list` |
| Graph groups | `ansible-inventory -i script.py --graph` |
| Run playbook via runner | `ansible_runner.run(playbook="site.yml", inventory="inv.py")` |
| Dry run | `run_playbook.py --check` |
| Limit hosts | `ansible-playbook site.yml -l webservers` |

**Next:** [Day 22 — pytest for infrastructure code](../day22/)
