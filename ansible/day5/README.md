# Day 5 — Blocks, Tags, Vault & Error Handling

**Goal:** Control playbook flow with blocks and tags, encrypt secrets with Ansible Vault, handle failures professionally, and run rolling updates.

**Time:** 5–6 hours (theory + hands-on)

---

## 1. Blocks: rescue and always

Blocks group tasks and add **try/catch/finally** semantics.

```yaml
- name: Deploy with rollback on failure
  block:
    - name: Upload new release
      ansible.builtin.copy:
        src: "{{ release_artifact }}"
        dest: /opt/app/releases/{{ deploy_version }}.tar.gz

    - name: Activate release
      ansible.builtin.file:
        src: "/opt/app/releases/{{ deploy_version }}"
        dest: /opt/app/current
        state: link

  rescue:
    - name: Log deploy failure
      ansible.builtin.debug:
        msg: "Deploy failed on {{ inventory_hostname }} — check logs"

    - name: Notify ops (example)
      ansible.builtin.uri:
        url: "{{ slack_webhook_url }}"
        method: POST
        body_format: json
        body:
          text: "Deploy failed: {{ inventory_hostname }}"
      delegate_to: localhost
      when: slack_webhook_url is defined
      ignore_errors: true

  always:
    - name: Record deploy attempt timestamp
      ansible.builtin.copy:
        content: "{{ ansible_date_time.iso8601 }}\n"
        dest: /var/log/handbook-last-deploy.txt
        mode: "0644"
```

- **block** — normal tasks
- **rescue** — runs if any block task fails
- **always** — runs regardless of success/failure

---

## 2. Tags

Tag tasks, roles, or blocks to run subsets:

```yaml
- name: Install nginx
  ansible.builtin.apt:
    name: nginx
    state: present
  tags: [packages, nginx]

- role: app_deploy
  tags: [app, deploy]
```

Run:

```bash
ansible-playbook site.yml --tags nginx
ansible-playbook site.yml --tags "packages,app"
ansible-playbook site.yml --skip-tags deploy
ansible-playbook site.yml --tags never_run_except_manual
```

Special tag `always` runs unless you `--skip-tags always`.

**CI pattern:** `--tags deploy` for app-only pipeline; full convergence weekly.

---

## 3. Strategies and rolling updates

Default **linear**: all hosts run task 1, then all run task 2.

```yaml
- hosts: webservers
  serial: "25%"   # or serial: 1 for one-at-a-time
  max_fail_percentage: 0
  order: sorted
  tasks:
    # ...
```

| Strategy | Behavior |
|----------|----------|
| `linear` (default) | Each task on all hosts before next task |
| `free` | Hosts proceed independently (`strategy: free`) |
| `serial` | Batch size for rolling updates |

```bash
ansible-playbook site.yml -e "serial=1"
```

---

## 4. Error handling

```yaml
- name: Check disk space
  ansible.builtin.command: df -h /
  register: df_out
  changed_when: false
  failed_when: false

- name: Fail if disk critical
  ansible.builtin.fail:
    msg: "Disk usage critical on {{ inventory_hostname }}"
  when: "'9[0-9]%' in df_out.stdout"

- name: Optional cleanup
  ansible.builtin.file:
    path: /tmp/old-cache
    state: absent
  ignore_errors: true

- name: Custom changed detection
  ansible.builtin.command: /opt/refresh-cache.sh
  register: cache_refresh
  changed_when: "'UPDATED' in cache_refresh.stdout"
  failed_when: cache_refresh.rc > 1
```

| Directive | Effect |
|-----------|--------|
| `failed_when` | Override failure condition |
| `changed_when` | Override change reporting |
| `ignore_errors: true` | Continue play on failure |
| `any_errors_fatal: true` | Stop all hosts on first failure |
| `max_fail_percentage` | Tolerate partial fleet failure |

---

## 5. Ansible Vault

Encrypt sensitive files at rest in Git.

```bash
# Create encrypted file
ansible-vault create group_vars/webservers/vault.yml

# Edit
ansible-vault edit group_vars/webservers/vault.yml

# Encrypt existing file
ansible-vault encrypt group_vars/webservers/secrets.yml

# View without edit
ansible-vault view group_vars/webservers/vault.yml
```

Example `vault.yml` content:

```yaml
---
db_password: "SuperSecret123!"
api_key: "sk-live-xxxxx"
```

Reference in plain vars:

```yaml
# group_vars/webservers.yml
db_password: "{{ vault_db_password }}"
```

Or load automatically — Ansible auto-decrypts vars from encrypted files when named conventionally.

Run playbooks:

```bash
ansible-playbook site.yml --ask-vault-pass
ansible-playbook playbooks/site.yml --vault-password-file ~/.ansible-vault-pass
export ANSIBLE_VAULT_PASSWORD_FILE=~/.ansible-vault-pass
```

**Never commit:** vault password file, `.vault-pass`, unencrypted secrets.

### Vault in CI

Store vault password in GitHub Actions secret / GitLab CI variable; write to temp file at job start; delete in `after_script`.

```yaml
# .github/workflows/ansible.yml (preview — Day 7)
- name: Run playbook
  env:
    ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
  run: |
    echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault-pass
    chmod 600 /tmp/vault-pass
    ansible-playbook site.yml --vault-password-file /tmp/vault-pass
    rm -f /tmp/vault-pass
```

### Encrypt strings inline

```bash
ansible-vault encrypt_string 'mysecret' --name 'db_password'
```

Paste output into vars file.

---

## 6. Delegation and localhost

Run a task on a different host than the play target:

```yaml
- name: Remove from load balancer
  ansible.builtin.uri:
    url: "http://lb-api/drain/{{ inventory_hostname }}"
    method: POST
  delegate_to: localhost
  run_once: true
```

| Directive | Purpose |
|-----------|---------|
| `delegate_to: localhost` | Control node executes module |
| `run_once: true` | Run one time, not per host |
| `local_action` | Legacy alias for delegate |

---

## 7. `meta` tasks

```yaml
- name: Flush handlers now
  ansible.builtin.meta: flush_handlers

- name: Clear facts after hostname change
  ansible.builtin.meta: clear_facts

- name: Refresh inventory mid-play
  ansible.builtin.meta: refresh_inventory
```

---

## 8. Lab — Day 5

From `ansible/day5/labs/`:

1. Create vault file: `ansible-vault create group_vars/webservers/vault.yml` with `vault_app_secret: handbook-day5`.
2. Reference secret in `templates/app.env.j2` via `{{ vault_app_secret }}`.
3. Run `ansible-playbook playbooks/deploy.yml --ask-vault-pass`.
4. Run with `--tags config` only — confirm packages skipped.
5. Run with `--check` and `--diff` — inspect template diff.
6. Simulate failure: set invalid nginx config in block; observe `rescue` message in output.
7. Re-run with `serial=1` on two hosts — watch rolling order in logs.

**Stretch:** Encrypt `db_password` with `encrypt_string` and embed in playbook vars.

---

## 9. DevOps connections

- **Secrets rotation:** Vault files in Git + automated re-encrypt job; prefer external secret stores (HashiCorp Vault, AWS SSM) for dynamic secrets.
- **Progressive delivery:** `serial` + health checks in blocks mirror canary deploys.
- **Blast radius:** `max_fail_percentage: 0` on prod; higher only in dev.

---

## Quick reference

| Task | Command |
|------|---------|
| Create vault | `ansible-vault create FILE` |
| Run with vault | `ansible-playbook site.yml --ask-vault-pass` |
| Tag run | `ansible-playbook site.yml --tags TAG` |
| Rolling | `serial: 1` in play |
| Encrypt string | `ansible-vault encrypt_string 'x' --name 'var'` |

**Previous:** [Day 4 — Roles](../day4/) · **Next:** [Day 6 — Dynamic inventory & collections](../day6/)
