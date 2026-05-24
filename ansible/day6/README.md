# Day 6 — Dynamic Inventory, Collections & Plugins

**Goal:** Generate inventory from live sources (cloud, scripts, plugins), install and use Ansible collections, and extend Ansible with custom filters and inventory plugins.

**Time:** 5–6 hours (theory + hands-on)

---

## 1. Static vs dynamic inventory

| Static | Dynamic |
|--------|---------|
| `hosts.yml` in Git | Generated from AWS, Azure, GCP, CMDB |
| Stable lab environments | Ephemeral autoscaling fleets |
| Manual updates | Always current instance list |

Dynamic inventory answers: **"What exists right now?"** Static inventory answers: **"What do we name our known servers?"**

Many teams use **hybrid**: dynamic discovery + `host_vars` in Git keyed by name tag.

---

## 2. Inventory plugins (modern approach)

Ansible 2.x prefers **inventory plugins** over legacy `inventory_script` executables.

`inventory/aws_ec2.yml`:

```yaml
---
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
filters:
  tag:Project: devops-handbook
  instance-state-name: running
keyed_groups:
  - key: tags.Role
    prefix: role
  - key: placement.region
    prefix: aws_region
hostnames:
  - tag:Name
compose:
  ansible_host: public_ip_address | default(private_ip_address)
```

Run:

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph
ansible-inventory -i inventory/aws_ec2.yml --list
ansible -i inventory/aws_ec2.yml role_webservers -m ping
```

Requires collection:

```bash
ansible-galaxy collection install amazon.aws
```

### Other common plugins

| Plugin | Collection | Source |
|--------|------------|--------|
| `azure.azcollection.azure_rm` | `azure.azcollection` | Azure VMs |
| `google.cloud.gcp_compute` | `google.cloud` | GCP instances |
| `community.docker.docker_containers` | `community.docker` | Local Docker |
| `constructed` | `ansible.builtin` | Transform other inventory |

---

## 3. Legacy inventory script pattern

Still seen in older codebases — executable returns JSON:

```bash
./inventory/docker_dynamic.py --list
```

`ansible.cfg`:

```ini
[defaults]
inventory = inventory/docker_dynamic.py
```

Prefer migrating to inventory plugins when possible.

---

## 4. Constructed inventory

Build groups from facts/vars on top of another inventory:

```yaml
---
plugin: constructed
strict: false
groups:
  primary_web: inventory_hostname.startswith('web') and (primary | default(false))
  low_memory: ansible_memtotal_mb < 2048
```

---

## 5. Collections

Collections package modules, plugins, and roles under a namespace.

```bash
ansible-galaxy collection install community.general
ansible-galaxy collection install kubernetes.core
ansible-galaxy collection install -r requirements.yml
```

`requirements.yml`:

```yaml
---
collections:
  - name: community.general
    version: "8.6.0"
  - name: community.docker
    version: "3.10.0"
  - name: amazon.aws
    version: "7.6.0"
```

List installed:

```bash
ansible-galaxy collection list
```

Use FQCN in playbooks:

```yaml
- name: Update Docker image
  community.docker.docker_image:
    name: nginx:1.25
    source: pull
```

---

## 6. `ansible-navigator` and execution environments (preview)

Enterprise teams package Ansible + collections + Python deps into **Execution Environments** (container images) for AWX/AAP consistency. Same idea as pinning `requirements.yml` in CI.

---

## 7. Custom filter plugin (control node)

`filter_plugins/custom_filters.py`:

```python
def to_upper_snake(value):
    """Convert my-var to MY_VAR style."""
    if not value:
        return value
    return str(value).replace('-', '_').upper()

class FilterModule(object):
    def filters(self):
        return {'to_upper_snake': to_upper_snake}
```

Use in template:

```jinja2
{{ app_name | to_upper_snake }}
```

Place `filter_plugins/` adjacent to playbook or in role.

---

## 8. Fact caching

Speed up large runs when facts change rarely:

```ini
[defaults]
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 86400
```

Invalidate when hardware or network changes materially.

---

## 9. Lab — Day 6

From `ansible/day6/labs/`:

### Part A — Docker dynamic inventory (local)

1. `pip install docker` on control node (for Docker API).
2. `ansible-galaxy collection install community.docker`.
3. Start lab containers: `docker compose -f docker-compose.lab.yml up -d`
4. `ansible-inventory -i inventory/docker.yml --graph`
5. `ansible -i inventory/docker.yml all -m ping`

### Part B — AWS (optional, if AWS account available)

1. `ansible-galaxy collection install amazon.aws`.
2. Configure AWS credentials (`aws configure` or env vars).
3. Tag two EC2 instances `Project=devops-handbook`, `Role=web`.
4. Edit `inventory/aws_ec2.yml` and run `ansible-inventory -i inventory/aws_ec2.yml --graph`.

### Part C — Collections in playbook

1. Run `ansible-playbook playbooks/ping-docker.yml` using `community.docker.docker_container_info` or `ansible.builtin.ping`.

**Stretch:** Add `constructed` inventory layer that groups containers by label `handbook.role`.

---

## 10. DevOps connections

- **Autoscaling:** New instances appear in dynamic inventory; Ansible or AWX job template runs on schedule or EventBridge trigger.
- **Kubernetes:** `kubernetes.core.k8s` module manages manifests; nodes may still be configured with `ansible-playbook` at join time.
- **Multi-cloud:** One repo, multiple inventory files: `-i aws_ec2.yml -i azure_rm.yml` with merge.

---

## Quick reference

| Task | Command |
|------|---------|
| Install collection | `ansible-galaxy collection install NAMESPACE.NAME` |
| List inventory | `ansible-inventory -i FILE --graph` |
| Ad-hoc dynamic | `ansible -i PLUGIN.yml GROUP -m ping` |
| Install from file | `ansible-galaxy collection install -r requirements.yml` |

**Previous:** [Day 5 — Vault & tags](../day5/) · **Next:** [Day 7 — Production & capstone](../day7/)
