# Day 3 — Variables, Facts, Jinja2 Templates & Loops

**Goal:** Parameterize playbooks with variables and facts, render config files with Jinja2 templates, and iterate with loops and conditionals.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. Variable precedence (simplified)

When the same variable is defined in multiple places, Ansible picks the **highest precedence** winner. Full list is long; remember these for daily work:

| Precedence (low → high) | Source |
|-------------------------|--------|
| Role defaults | `roles/x/defaults/main.yml` |
| Inventory group/host vars | `inventory/`, `group_vars/`, `host_vars/` |
| Play vars | `vars:` in playbook |
| Task vars | `vars:` on task |
| `-e` / `--extra-vars` | CLI (highest — wins) |

```bash
ansible-playbook playbooks/vhosts.yml -e "http_port=9090"
```

**Best practice:** Defaults in role `defaults/`, environment overrides in `group_vars/staging.yml`, secrets in Vault (Day 5).

---

## 2. Where to store variables

```
inventory/
  hosts.yml
group_vars/
  webservers.yml      # all hosts in group webservers
  all.yml               # every host
host_vars/
  web1.yml              # only web1
playbooks/
  vhosts.yml
```

Example `group_vars/webservers.yml`:

```yaml
---
http_port: 80
app_name: handbook
vhosts:
  - name: app1
    server_name: app1.localdev.me
    root: /var/www/app1
  - name: app2
    server_name: app2.localdev.me
    root: /var/www/app2
```

Example `host_vars/web1.yml`:

```yaml
---
primary: true
http_port: 8080   # overrides group var for web1 only
```

---

## 3. Facts

Facts are variables Ansible collects from each host via the `setup` module (runs automatically when `gather_facts: true`).

```yaml
- name: Print OS
  ansible.builtin.debug:
    msg: "{{ ansible_distribution }} {{ ansible_distribution_version }}"

- name: Print memory
  ansible.builtin.debug:
    msg: "RAM: {{ ansible_memtotal_mb }} MB"
```

Useful fact namespaces:

| Fact | Example use |
|------|-------------|
| `ansible_os_family` | Debian vs RedHat branching |
| `ansible_default_ipv4.address` | Bind address in templates |
| `ansible_hostname` | Logging, labels |
| `ansible_mounts` | Disk checks |
| `ansible_processor_vcpus` | Tuning worker counts |

Gather subset only (faster):

```yaml
- name: Gather minimal facts
  ansible.builtin.setup:
    gather_subset:
      - "!all"
      - network
```

Disable when unused:

```yaml
- hosts: webservers
  gather_facts: false
```

### Custom facts

Drop executable scripts in `/etc/ansible/facts.d/*.fact` on the target — they become `ansible_local`.

### `register` and `set_fact`

```yaml
- name: Check nginx config
  ansible.builtin.command: nginx -t
  register: nginx_test
  changed_when: false

- name: Fail if nginx config invalid
  ansible.builtin.fail:
    msg: "{{ nginx_test.stderr }}"
  when: nginx_test.rc != 0

- name: Remember deploy version
  ansible.builtin.set_fact:
    deploy_version: "{{ lookup('env', 'BUILD_ID') | default('dev', true) }}"
```

---

## 4. Jinja2 templates

The `template` module renders `.j2` files on the control node and copies result to the target.

```jinja2
{# templates/nginx-vhost.conf.j2 #}
server {
    listen {{ http_port }};
    server_name {{ item.server_name }};

    root {{ item.root }};
    index index.html;

    access_log /var/log/nginx/{{ item.name }}_access.log;
    error_log  /var/log/nginx/{{ item.name }}_error.log;

{% if primary | default(false) %}
    # Primary node — stricter timeouts
    client_body_timeout 10s;
{% endif %}

    location / {
        try_files $uri $uri/ =404;
    }
}
```

Playbook usage:

```yaml
- name: Deploy vhost configs
  ansible.builtin.template:
    src: nginx-vhost.conf.j2
    dest: "/etc/nginx/sites-available/{{ item.name }}.conf"
    mode: "0644"
  loop: "{{ vhosts }}"
  notify: Reload nginx
```

### Jinja2 essentials

```jinja2
{{ variable }}                          {# output #}
{{ list | join(',') }}                  {# filter #}
{% if condition %} ... {% endif %}      {# logic #}
{% for x in items %} ... {% endfor %}   {# loop in template #}
{# comment #}
{{ default_var | default('fallback') }}
```

Common filters: `default`, `mandatory`, `upper`, `lower`, `trim`, `to_json`, `b64encode`, `hash`.

---

## 5. Loops

Modern style uses `loop` (replaces legacy `with_*`):

```yaml
- name: Create app directories
  ansible.builtin.file:
    path: "{{ item.root }}"
    state: directory
    owner: www-data
    group: www-data
    mode: "0755"
  loop: "{{ vhosts }}"
  loop_control:
    label: "{{ item.name }}"
```

`loop_control.label` keeps output readable in large loops.

### Loop with `register`

```yaml
- name: Deploy each vhost
  ansible.builtin.template:
    src: nginx-vhost.conf.j2
    dest: "/etc/nginx/sites-available/{{ item.name }}.conf"
  loop: "{{ vhosts }}"
  register: vhost_results

- name: Show changed vhosts
  ansible.builtin.debug:
    msg: "{{ item.item.name }} changed={{ item.changed }}"
  loop: "{{ vhost_results.results }}"
  when: item.changed
```

### `dict2items` for dict loops

```yaml
users:
  alice: admin
  bob: deploy

- name: Create users
  ansible.builtin.user:
    name: "{{ item.key }}"
    groups: "{{ item.value }}"
  loop: "{{ users | dict2items }}"
```

---

## 6. Conditionals (`when`)

```yaml
- name: Install firewalld (RHEL only)
  ansible.builtin.dnf:
    name: firewalld
    state: present
  when: ansible_os_family == "RedHat"

- name: Reload on primary only
  ansible.builtin.service:
    name: nginx
    state: reloaded
  when: primary | default(false) | bool
```

Combine conditions:

```yaml
when:
  - ansible_os_family == "Debian"
  - http_port | int > 1024
```

---

## 7. Lookups (preview)

```yaml
# Environment variable
deploy_env: "{{ lookup('env', 'DEPLOY_ENV') | default('dev', true) }}"

# File on control node
ssl_cert: "{{ lookup('file', 'files/cert.pem') }}"

# Pipe (careful — runs shell on control node)
git_sha: "{{ lookup('pipe', 'git rev-parse --short HEAD') }}"
```

Secrets belong in Vault, not plain files (Day 5).

---

## 8. Lab — Day 3

From `ansible/day3/labs/`:

1. Review `group_vars/webservers.yml` — two vhosts defined.
2. `ansible-playbook playbooks/vhosts.yml --syntax-check`
3. Run with `--check --diff`; inspect rendered nginx configs on targets.
4. Run for real; `curl -H "Host: app1.localdev.me" http://WEB1_IP/`
5. Add `primary: true` in `host_vars/web1.yml`; re-run; confirm only web1 template diff shows timeout block.
6. Add a third vhost in group vars; re-run — only new vhost tasks should change.

**Stretch:** Use `register` to fail the play if zero vhosts are defined (`when: vhosts | length == 0`).

---

## 9. DevOps connections

- **12-factor config:** Environment-specific values in `group_vars/production.yml`, not hardcoded in roles.
- **Feature flags:** Template conditionals toggle features per group (`staging` vs `prod`).
- **Kubernetes:** Same Jinja2 skills apply to Helm Go templates — different engine, same mindset (Day 18 in Kubernetes handbook).

---

## Quick reference

| Task | Pattern |
|------|---------|
| Group vars | `group_vars/GROUP.yml` |
| Host override | `host_vars/HOST.yml` |
| Template | `template: src=x.j2 dest=y` |
| Loop | `loop: "{{ items }}"` |
| Conditional | `when: expression` |
| Extra var | `-e key=value` |

**Previous:** [Day 2 — Playbooks](../day2/) · **Next:** [Day 4 — Roles & Galaxy](../day4/)
