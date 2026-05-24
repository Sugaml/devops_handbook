# Day 4 — Roles, Galaxy & Reusable Automation

**Goal:** Refactor playbooks into roles, use standard directory layout, consume community roles from Ansible Galaxy, and compose multi-role playbooks.

**Time:** 5–6 hours (theory + hands-on)

---

## 1. Why roles?

| Monolithic playbook | Role |
|---------------------|------|
| 300-line YAML file | Focused directories per concern |
| Copy-paste between projects | `ansible-galaxy install` / Git submodule |
| Hard to test in isolation | Molecule tests per role (Day 7) |
| Unclear defaults vs overrides | `defaults/` vs `vars/` |

A **role** is the standard unit of reuse in Ansible — how platform teams ship "nginx baseline" or "CIS hardening" across hundreds of repos.

---

## 2. Role directory layout

```
roles/
  nginx/
    defaults/main.yml       # low precedence defaults (document all knobs)
    vars/main.yml           # role internal vars (higher precedence, rarely change)
    tasks/main.yml          # entry task list
    handlers/main.yml
    templates/*.j2
    files/*                 # static files (copy module)
    meta/main.yml           # dependencies, Galaxy metadata
    README.md
```

Minimal `roles/nginx/tasks/main.yml`:

```yaml
---
- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ ansible_os_family }}.yml"
  failed_when: false

- name: Install nginx
  ansible.builtin.include_tasks: install-{{ ansible_os_family }}.yml

- name: Configure nginx
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: "{{ nginx_conf_path }}"
    mode: "0644"
  notify: Reload nginx
```

Use `include_tasks` for large roles — keeps `main.yml` readable.

---

## 3. Using roles in playbooks

```yaml
---
- name: Web stack
  hosts: webservers
  become: true
  roles:
    - role: common
    - role: nginx
      vars:
        nginx_vhosts: "{{ vhosts }}"
    - role: app_deploy
      tags: [app]
```

Order matters — roles run in listed order.

### `import_role` vs `roles:` keyword

```yaml
tasks:
  - name: Run nginx role after pre-check
    ansible.builtin.import_role:
      name: nginx
    vars:
      http_port: 8080
```

Use `import_role` when you need a role **between specific tasks**, not at play start.

---

## 4. defaults vs vars

| Directory | Purpose | Override? |
|-----------|---------|-----------|
| `defaults/main.yml` | User-facing knobs | Easy — inventory, `-e` |
| `vars/main.yml` | Internal constants | Harder — intentional |

```yaml
# roles/nginx/defaults/main.yml
nginx_vhosts: []
http_port: 80
nginx_conf_path: /etc/nginx/nginx.conf

# roles/nginx/vars/main.yml
nginx_package: nginx
```

Document every default in the role README — platform consumers depend on it.

---

## 5. Role dependencies

`roles/nginx/meta/main.yml`:

```yaml
---
dependencies:
  - role: common
    vars:
      common_packages:
        - curl
        - ca-certificates
  - role: geerlingguy.firewall
    when: nginx_manage_firewall | default(false)
```

Dependencies run **before** the role that declares them.

---

## 6. Ansible Galaxy

Galaxy hosts community roles and collections.

```bash
# Search
ansible-galaxy search nginx --author geerlingguy

# Install role to ./roles/
ansible-galaxy role install geerlingguy.nginx -p roles/

# requirements file
ansible-galaxy role install -r requirements.yml -p roles/
```

`requirements.yml`:

```yaml
---
roles:
  - name: geerlingguy.nginx
    version: "3.2.0"
  - name: geerlingguy.security
    version: "2.0.0"

collections:
  - name: community.general
    version: ">=8.0.0"
```

**Production:** Pin versions. Audit role content before use — you are trusting arbitrary YAML with root on your servers.

---

## 7. Scaffold a new role

```bash
cd ansible/day4/labs
ansible-galaxy role init nginx --role-skeleton=default
# or manually match layout in labs/roles/
```

Galaxy metadata (`meta/main.yml`):

```yaml
galaxy_info:
  author: devops-handbook
  description: Nginx baseline for handbook labs
  license: MIT
  min_ansible_version: "2.15"
  platforms:
    - name: Ubuntu
      versions: [jammy, noble]
dependencies: []
```

---

## 8. Project layout (multi-role)

```
ansible/day4/labs/
  ansible.cfg
  inventory/
  group_vars/
  site.yml                 # top-level playbook
  roles/
    common/
    nginx/
    app_deploy/
  requirements.yml
```

`site.yml`:

```yaml
---
- name: Apply web stack
  hosts: webservers
  become: true
  roles:
    - common
    - nginx
    - app_deploy
```

Run:

```bash
ansible-playbook site.yml
ansible-playbook site.yml --tags nginx
```

---

## 9. Lab — Day 4

From `ansible/day4/labs/`:

1. `ansible-galaxy role install -r requirements.yml -p roles/` (optional community role) or use bundled `roles/nginx`.
2. Compare Day 2 monolithic playbook with `roles/nginx/tasks/main.yml`.
3. `ansible-playbook site.yml --syntax-check && ansible-playbook site.yml`
4. Verify web content and both vhosts from Day 3 vars in `group_vars/webservers.yml`.
5. Create a tiny `roles/common` task that sets timezone to UTC (or installs `htop`) — run before nginx via role order.
6. Re-run site.yml — confirm idempotency.

**Stretch:** Publish your `nginx` role as a Git repo and install via `requirements.yml` with `src: git+https://...`.

---

## 10. DevOps connections

- **Internal Galaxy / Git:** Enterprises run private Automation Hub or Artifactory for approved roles.
- **Composition:** Terraform provisions → `site.yml` configures → CI runs Molecule on every PR (Day 7).
- **Version pins:** Same as Helm chart versions — bump role version in requirements, not `latest`.

---

## Quick reference

| Task | Command |
|------|---------|
| Init role | `ansible-galaxy role init NAME` |
| Install role | `ansible-galaxy role install user.role -p roles/` |
| Install from file | `ansible-galaxy role install -r requirements.yml` |
| Run site | `ansible-playbook site.yml` |

**Previous:** [Day 3 — Variables & templates](../day3/) · **Next:** [Day 5 — Blocks, tags & Vault](../day5/)
