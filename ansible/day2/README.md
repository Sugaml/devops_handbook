# Day 2 — Playbooks, Tasks, Modules & Handlers

**Goal:** Write your first playbooks, understand YAML structure for Ansible, use common modules, and trigger handlers on change.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. Why playbooks?

| Ad-hoc | Playbook |
|--------|----------|
| One task, one command line | Ordered multi-step automation |
| Hard to review in Git | YAML in PRs, code review |
| No reuse | Import roles, vars, templates |
| No tags or rolling strategy | Production orchestration |

Playbooks are **the unit of automation** in Ansible — version them, test them, run them from CI.

---

## 2. Playbook anatomy

```yaml
---
- name: Configure web servers          # Play name (optional but recommended)
  hosts: webservers                    # Inventory pattern
  become: true                         # sudo for all tasks in play
  gather_facts: true                   # default: collect setup facts

  vars:
    app_port: 8080

  tasks:
    - name: Ensure nginx is installed
      ansible.builtin.apt:
        name: nginx
        state: present
        update_cache: true

    - name: Ensure nginx is running
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true
```

Execution flow:

```
ansible-playbook site.yml
    → parse YAML
    → for each play: select hosts
    → gather facts (unless disabled)
    → run tasks in order on each host (linear strategy)
    → run handlers (once, at end of play, if notified)
```

---

## 3. YAML rules for Ansible

1. **Indentation with spaces** — never tabs. Use 2 spaces per level.
2. **Lists** start with `- `.
3. **Key-value** pairs use `key: value`.
4. **Strings** with `:`, `{`, `[`, or leading `#` may need quotes.
5. **Booleans:** `true` / `false` (not `yes`/`no` in modern Ansible, though legacy accepts both).

```yaml
# Good
- name: Set timezone
  ansible.builtin.timezone:
    name: UTC

# Bad — inconsistent indent
- name: Broken
   ansible.builtin.debug:
     msg: hello
```

Validate before running:

```bash
ansible-playbook playbooks/webserver.yml --syntax-check
```

---

## 4. Running playbooks

```bash
cd ansible/day2/labs

ansible-playbook playbooks/webserver.yml
ansible-playbook playbooks/webserver.yml --check --diff
ansible-playbook playbooks/webserver.yml --limit web1
ansible-playbook playbooks/webserver.yml -v    # -vvv for module args
ansible-playbook playbooks/webserver.yml --start-at-task "Ensure nginx is running"
```

| Flag | Purpose |
|------|---------|
| `--check` | Dry run |
| `--diff` | Show file changes |
| `--limit` | Subset of hosts |
| `--tags` / `--skip-tags` | Run tagged tasks only (Day 5) |
| `--step` | Confirm each task interactively |

---

## 5. Essential modules (Day 2 set)

### Package management

```yaml
- name: Install packages (Debian/Ubuntu)
  ansible.builtin.apt:
    name:
      - nginx
      - curl
    state: present
    update_cache: true
  when: ansible_os_family == "Debian"

- name: Install packages (RHEL family)
  ansible.builtin.dnf:
    name: nginx
    state: present
  when: ansible_os_family == "RedHat"
```

### Files and directories

```yaml
- name: Create document root
  ansible.builtin.file:
    path: /var/www/handbook
    state: directory
    owner: www-data
    group: www-data
    mode: "0755"

- name: Deploy static index page
  ansible.builtin.copy:
    src: files/index.html
    dest: /var/www/handbook/index.html
    owner: www-data
    group: www-data
    mode: "0644"
```

### Service management

```yaml
- name: Enable and start nginx
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: true
```

### Commands and debugging

```yaml
- name: Print hostname
  ansible.builtin.debug:
    msg: "Configuring {{ inventory_hostname }} ({{ ansible_default_ipv4.address }})"
```

---

## 6. Handlers

Handlers run **at the end of the play**, **only once**, and **only if notified** by a task that changed.

```yaml
  tasks:
    - name: Deploy nginx config
      ansible.builtin.template:
        src: templates/nginx-site.conf.j2
        dest: /etc/nginx/sites-available/handbook.conf
      notify: Reload nginx

  handlers:
    - name: Reload nginx
      ansible.builtin.service:
        name: nginx
        state: reloaded
```

**Why handlers?** Avoid restarting a service on every task when nothing changed. Restart only when config actually changed.

**Handler naming:** The `notify` string must match the handler `name` exactly.

**Force all handlers:** `meta: flush_handlers` runs pending handlers immediately (useful mid-play).

```yaml
- name: Flush handlers before health check
  ansible.builtin.meta: flush_handlers
```

---

## 7. Multiple plays in one file

```yaml
---
- name: Web tier
  hosts: webservers
  become: true
  tasks:
  # ...

- name: Database tier
  hosts: dbservers
  become: true
  tasks:
  # ...
```

Each play can target different groups with different vars and become settings.

---

## 8. Module documentation

```bash
ansible-doc apt
ansible-doc -l | grep nginx
ansible-doc ansible.builtin.copy
```

Online: [docs.ansible.com](https://docs.ansible.com/ansible/latest/collections/index.html)

**FQCN** (Fully Qualified Collection Name): `ansible.builtin.copy` vs legacy `copy`. Both work if `ansible.builtin` is implicit; prefer FQCN in production playbooks.

---

## 9. Idempotency patterns

| Pattern | Example |
|---------|---------|
| `state: present` | Package installed |
| `state: absent` | File removed |
| `creates:` on command | Skip if file exists |
| `changed_when: false` | Always report ok |
| `register` + `when` | Conditional follow-up (Day 3) |

```yaml
- name: Run install script once
  ansible.builtin.command: /opt/install.sh
  args:
    creates: /opt/.installed
```

Run playbook twice — second run should show `changed=0` for most tasks.

---

## 10. Check mode caveats

Not every module supports `--check`. Read module docs for `supports_check_mode`.

```bash
ansible-playbook playbooks/webserver.yml --check
```

If a task fails in check mode, add `check_mode: no` on that task only when necessary (e.g. some `command` tasks).

---

## 11. Lab — Day 2

From `ansible/day2/labs/`:

1. Update `inventory/hosts.yml` with your web server IPs (copy from Day 1).
2. `ansible-playbook playbooks/webserver.yml --syntax-check`
3. Run with `--check --diff`, then for real.
4. `curl http://WEB1_IP/` — see "Ansible Handbook — Day 2".
5. Run playbook again; confirm `changed=0`.
6. Edit `files/index.html`; re-run; confirm only copy task changed and handler ran (if you add a notify on copy in stretch goal).

**Stretch:** Add a second play for `dbservers` that installs `postgresql` (or `sqlite` package only) and creates `/var/lib/handbook` directory.

---

## 12. DevOps connections

- **GitOps:** Playbooks live in Git; `ansible-playbook` runs from CI after merge (Day 7).
- **Rolling deploys:** Same playbook, run with `--limit` per batch or use `serial` (Day 5).
- **Configuration drift:** Scheduled playbook runs detect and fix drift — complementary to immutable images.

---

## Quick reference

| Task | Command |
|------|---------|
| Syntax check | `ansible-playbook site.yml --syntax-check` |
| Dry run | `ansible-playbook site.yml --check --diff` |
| Verbose | `ansible-playbook site.yml -vvv` |
| Module help | `ansible-doc MODULE` |

**Previous:** [Day 1 — Inventory & ad-hoc](../day1/) · **Next:** [Day 3 — Variables, facts & templates](../day3/)
