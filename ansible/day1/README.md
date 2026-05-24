# Day 1 — Ansible Concepts, Install, Inventory & Ad-Hoc Commands

**Goal:** Understand how Ansible works, install it on a control node, define inventory, and run ad-hoc commands against real hosts.

**Time:** 4–5 hours (theory + hands-on)

---

## 1. What is Ansible?

| Traditional scripting | Ansible |
|----------------------|---------|
| Imperative: "run these commands" | Declarative: "ensure this state" |
| Custom SSH loops per host | Built-in parallelism and inventory |
| Idempotency is your problem | Modules are idempotent by design |
| Agent installed on every server | **Agentless** — uses SSH (Linux) or WinRM (Windows) |

Ansible is **configuration management and orchestration** software. You describe desired state in YAML; Ansible figures out what to change.

```
  Control node                    Managed nodes
  ┌─────────────┐                ┌──────────────┐
  │ ansible     │  SSH / WinRM   │ web1         │
  │ playbooks   │ ─────────────► │ web2         │
  │ inventory   │                │ db1          │
  └─────────────┘                └──────────────┘
        │
        └── No daemon required on targets
```

**DevOps use cases:**

- Bootstrap new VMs after Terraform/CloudFormation creates them
- Patch and harden fleets on a schedule
- Deploy application releases with rolling updates
- Enforce compliance (CIS benchmarks, package versions)

---

## 2. Core vocabulary

| Term | Meaning |
|------|---------|
| **Control node** | Machine where you install Ansible and run commands |
| **Managed node** | Host Ansible configures (not an Ansible server) |
| **Inventory** | List of hosts and groups |
| **Playbook** | YAML file of ordered tasks (Day 2) |
| **Task** | Single unit of work (one module call) |
| **Module** | Unit of code Ansible executes (`copy`, `apt`, `service`, …) |
| **Ad-hoc command** | One-liner task without a playbook |
| **Facts** | Auto-collected variables about a host (OS, IP, memory) |
| **Play** | Mapping of hosts → tasks in a playbook |
| **Role** | Reusable bundle of tasks, files, templates (Day 4) |

---

## 3. Architecture: push, parallelism, modules

1. You run `ansible` or `ansible-playbook` on the **control node**.
2. Ansible reads **inventory** and connects to each host (default: up to 5 forks in parallel).
3. Modules are copied to a temp directory on the target, executed, then cleaned up.
4. Results return as JSON; Ansible reports **ok**, **changed**, **failed**, or **skipped**.

```bash
# See default parallelism
grep forks ansible.cfg
# forks = 5

# Increase for large fleets (careful with API rate limits)
ansible-playbook site.yml -f 20
```

**Important:** Ansible does **not** need to run as root on the control node, but many tasks require **become** (sudo) on managed nodes.

---

## 4. Install Ansible

### macOS

```bash
brew install ansible
# or pinned via pip:
python3 -m pip install --user 'ansible-core>=2.15,<2.17'
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y ansible sshpass
ansible --version
```

### Python venv (recommended for projects)

```bash
python3 -m venv ~/.venvs/ansible
source ~/.venvs/ansible/bin/activate
pip install ansible ansible-lint
ansible --version
```

Verify:

```bash
ansible --version
# ansible [core 2.15.x]
python3 -c "import ansible; print('OK')"
```

---

## 5. Lab target setup

You need at least one reachable Linux host. Options:

### Option A — Cloud VM (recommended)

Launch Ubuntu 22.04/24.04 with your SSH key. Security group: allow SSH from your IP.

```bash
# On the VM (once), create ansible user — or use default 'ubuntu'
sudo useradd -m -s /bin/bash ansible
sudo mkdir -p /home/ansible/.ssh
sudo cp ~/.ssh/authorized_keys /home/ansible/.ssh/
sudo chown -R ansible:ansible /home/ansible/.ssh
echo 'ansible ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/ansible
```

### Option B — Multipass

```bash
multipass launch 24.04 --name ansible-web1 --cpus 1 --memory 1G
multipass info ansible-web1   # note IP
ssh ubuntu@$(multipass info ansible-web1 | awk '/IPv4/{print $2}')
```

### Option C — Second VM `web2`

Repeat for a second host to practice group patterns later.

Test SSH manually before Ansible:

```bash
ssh -i ~/.ssh/id_ed25519 ansible@WEB1_IP 'hostname && whoami'
```

---

## 6. Configuration: `ansible.cfg`

Ansible reads config from (highest precedence first):

1. `ANSIBLE_CONFIG` environment variable
2. `./ansible.cfg` in current directory
3. `~/.ansible.cfg`
4. `/etc/ansible/ansible.cfg`

Use a project-local file so labs are reproducible:

```ini
# ansible/day1/labs/ansible.cfg
[defaults]
inventory = inventory/hosts.yml
remote_user = ansible
private_key_file = ~/.ssh/id_ed25519
host_key_checking = False
retry_files_enabled = False
stdout_callback = yaml
interpreter_python = auto_silent

[privilege_escalation]
become = True
become_method = sudo
become_ask_pass = False

[ssh_connection]
pipelining = True
```

**Production note:** Enable `host_key_checking = True` and manage `known_hosts`. Disable pipelining only if sudo requires a TTY.

---

## 7. Inventory

Inventory defines **hosts**, **groups**, and **variables**.

### INI format

```ini
# inventory/hosts.ini
[webservers]
web1 ansible_host=192.168.1.10
web2 ansible_host=192.168.1.11

[dbservers]
db1 ansible_host=192.168.1.20

[webservers:vars]
ansible_user=ansible
http_port=80

[datacenter:children]
webservers
dbservers
```

### YAML format (preferred for complex inventory)

```yaml
# inventory/hosts.yml
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 192.168.1.10
        web2:
          ansible_host: 192.168.1.11
      vars:
        http_port: 80
    dbservers:
      hosts:
        db_nameserver:
          ansible_host: 192.168.1.20
```

### Host patterns

| Pattern | Matches |
|---------|---------|
| `web1` | Single host |
| `webservers` | All hosts in group |
| `webservers:dbservers` | Union |
| `webservers:&dbservers` | Intersection |
| `webservers:!web2` | Exclusion |
| `*.example.com` | Wildcard (limited) |
| `all` | Everything |

```bash
cd ansible/day1/labs
ansible-inventory --list
ansible-inventory --graph
ansible-inventory --host web1
```

---

## 8. Ad-hoc commands

Syntax:

```bash
ansible <pattern> -m <module> -a "<module args>"
```

### Connectivity

```bash
ansible all -m ping
# pong = success (not ICMP — it's an Ansible module)

ansible webservers -m ansible.builtin.setup -a "filter=ansible_distribution*"
```

### Command vs shell

```bash
# command — no shell features (no pipes, redirects)
ansible webservers -m command -a "uptime"

# shell — full shell (use sparingly; prefer dedicated modules)
ansible webservers -m shell -a "ps aux | grep nginx | grep -v grep"
```

**Rule:** Prefer **modules** over raw commands. `command`/`shell` skip idempotency unless you add `creates`/`removes`.

### Package and service (become required)

```bash
ansible webservers -m apt -a "name=nginx state=present update_cache=yes" -b
ansible webservers -m service -a "name=nginx state=started enabled=yes" -b
```

### Files

```bash
ansible webservers -m file -a "path=/var/www/handbook state=directory owner=www-data mode=0755" -b
ansible webservers -m copy -a "content='Hello Day 1\n' dest=/var/www/handbook/index.html mode=0644" -b
```

### User management

```bash
ansible webservers -m user -a "name=deploy shell=/bin/bash groups=sudo append=yes" -b
```

---

## 9. Essential flags

| Flag | Short | Purpose |
|------|-------|---------|
| `--inventory` | `-i` | Alternate inventory file |
| `--module-name` | `-m` | Module to run |
| `--args` | `-a` | Module arguments |
| `--become` | `-b` | Escalate privileges (sudo) |
| `--become-user` | | Run become as specific user |
| `--check` | `-C` | Dry run (no changes) |
| `--diff` | `-D` | Show file diffs |
| `--limit` | `-l` | Restrict to host pattern |
| `--user` | `-u` | SSH user override |
| `-vvv` | | Verbose SSH/debug.log |

Examples:

```bash
ansible webservers -m apt -a "name=nginx state=present" -b -C
ansible webservers -m copy -a "src=./index.html dest=/tmp/" --limit web1
ansible all -m ping -u ubuntu --private-key ~/.ssh/lab.pem
```

---

## 10. Idempotency in ad-hoc mode

Run the same command twice:

```bash
ansible webservers -m apt -a "name=nginx state=present update_cache=yes" -b
ansible webservers -m apt -a "name=nginx state=present update_cache=yes" -b
```

First run: `changed=1`. Second run: `changed=0`, `ok=1`.

If a module is not idempotent (e.g. `command: reboot`), use `creates` or move logic to a playbook with `changed_when`.

---

## 11. Troubleshooting SSH

```bash
# Verbose connection
ansible web1 -m ping -vvv

# Common fixes
# 1. Wrong key → set private_key_file in inventory or ansible.cfg
# 2. Wrong user → ansible_user=ubuntu
# 3. Python missing on target → ansible_python_interpreter=/usr/bin/python3
# 4. sudo password → --ask-become-pass or NOPASSWD in sudoers
```

Manual SSH test with same args Ansible uses:

```bash
ssh -i ~/.ssh/id_ed25519 ansible@WEB1_IP -o StrictHostKeyChecking=no
```

---

## 12. Lab — Day 1

Work from `ansible/day1/labs/`.
1. Copy `inventory/hosts.yml.example` to `inventory/hosts.yml` and set real `ansible_host` IPs.
2. Run `ansible-inventory --graph` and confirm groups.
3. `ansible all -m ping` — all hosts return `pong`.
4. Ad-hoc: create `/opt/handbook/day1.txt` with `copy` module containing today's date.
5. Ad-hoc: install `htop` with `apt` or `dnf` (use `-m package` with appropriate package manager or OS-specific module).
6. Run step 5 again with `-C`; confirm `changed=0` on second real run.
7. Gather facts: `ansible webservers -m setup -a "filter=ansible_memtotal_mb"` — record RAM per host.

**Stretch:** Add a `[dbservers]` host and use pattern `webservers:dbservers` for `ping`. Add host var `ansible_python_interpreter: /usr/bin/python3` on one host only.

---

## 13. DevOps connections

- **Immutable infra + Ansible:** Terraform creates servers; Ansible (or cloud-init) configures them — know where each tool stops.
- **Golden images:** Minimize Ansible first-boot time by baking common packages into AMI/Packer; Ansible handles drift and app config.
- **Audit:** Ad-hoc is for debugging; production changes go through versioned playbooks and CI (Day 7).

---

## Quick reference

| Task | Command
|------|------|
| Test connectivity | `ansible all -m ping` |
| Run command | `ansible HOST -m command -a "cmd"` |
| Install package | `ansible HOST -m apt -a "name=PKG state=present" -b` |
| Copy content | `ansible HOST -m copy -a "content=... dest=..." -b` |
| Dry run | add `-C` |
| List inventory | `ansible-inventory --graph` |

**Next:** [Day 2 — Playbooks, tasks, modules & handlers](../day2/)
