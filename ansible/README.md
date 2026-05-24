# Ansible for DevOps — 7-Day Handbook

A hands-on path from your first `ansible ping` to production-grade automation: roles, Vault, dynamic inventory, CI/CD, and platform patterns. Each day builds on the last with runnable playbooks and labs.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Concepts, install, inventory & ad-hoc commands | [day1](./day1/) |
| 2 | Playbooks, tasks, modules & handlers | [day2](./day2/) |
| 3 | Variables, facts, Jinja2 templates & loops | [day3](./day3/) |
| 4 | Roles, Galaxy & reusable automation | [day4](./day4/) |
| 5 | Blocks, tags, Vault & error handling | [day5](./day5/) |
| 6 | Dynamic inventory, collections & plugins | [day6](./day6/) |
| 7 | Production layout, testing, CI/CD & capstone | [day7](./day7/) |

## Prerequisites

- Comfort with Linux shell and SSH ([Linux handbook](../linux/README.md) Day 1–5 recommended).
- Basic YAML syntax (indentation matters — no tabs).
- One **control node** (your laptop or a VM) and at least one **managed node** (VM, cloud instance, or Docker container for labs).
- Python 3.9+ on the control node (Ansible 2.15+).

## How to use this handbook

1. Complete **Day 1** lab setup before anything else — inventory and SSH must work.
2. Work from the repo's `ansible/dayN/labs/` directories; copy or run in place.
3. Always run `ansible-playbook --syntax-check` and `--check` before applying changes.
4. Complete each day's **Lab** section before moving on.
5. Keep a personal cheat sheet of modules and patterns you reuse at work.

## Recommended lab setup

```bash
# Control node — macOS
brew install ansible sshpass
python3 -m pip install --user ansible ansible-lint

# Control node — Ubuntu/Debian
sudo apt update && sudo apt install -y ansible sshpass python3-pip
pip3 install --user ansible-lint

ansible --version
# ansible [core 2.15+]

# Optional: two Docker targets for local labs (Day 1)
docker run -d --name ansible-web1 --hostname web1 \
  -p 2221:22 quay.io/ansible/ansible-runner:latest sleep infinity 2>/dev/null || true

# Better lab targets: real VMs or Multipass
# multipass launch 22.04 --name ansible-web1 --cpus 1 --memory 1G
```

For persistent lab targets, use cloud VMs (EC2, Azure VM, GCP Compute) or Vagrant. Docker works for early days but lacks full `systemd` unless configured — Day 2+ labs assume a normal Linux VM with `systemd`.

## Project conventions in this handbook

| Convention | Value |
|------------|--------|
| Inventory group | `webservers` |
| Lab user | `ansible` (with sudo) or `ubuntu` on cloud images |
| SSH key | `~/.ssh/id_ed25519` (adjust in `ansible.cfg`) |
| Playbook namespace | `handbook` prefix on release names / paths |

Sample playbooks live under each day's `labs/` folder. Day 7 combines them into a production-style layout.

## Design notes

- **Ansible Core 2.15+** — FQCN modules (`ansible.builtin.copy`) used throughout; legacy short names noted where still common.
- **Agentless push model** — no daemon on managed nodes; SSH (Linux) or WinRM (Windows, not covered in depth here).
- **Idempotency** is the core skill: running a playbook twice should change nothing the second time.
- DevOps callouts map Ansible to config management, golden images, Kubernetes node prep, and CI pipelines.

## Progress checklist

```
[ ] Day 1  [ ] Day 4
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
[ ] Day 7 — capstone
```

## Related handbooks

| Handbook | Why it matters for Ansible |
|----------|----------------------------|
| [Linux](../linux/README.md) | SSH, systemd, packages — what playbooks automate |
| [Docker](../docker/README.md) | Container targets and image build pipelines |
| [Kubernetes](../kubernetes/README.md) | `kubernetes.core` collection, node prep playbooks |
| [AWS](../aws/README.md) | `amazon.aws` collection, EC2 dynamic inventory |
| [Git](../git/README.md) | Version control for playbooks and PR workflows |
