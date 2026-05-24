# Day 7 — Production Layout, Testing, CI/CD & Capstone

**Goal:** Structure Ansible for teams, lint and test automation, integrate with CI/CD and AWX/AAP, and complete a capstone multi-tier deploy.

**Time:** 6–8 hours (theory + capstone)

---

## 1. Production repository layout

```
ansible-production/
├── ansible.cfg
├── requirements.yml          # collections + roles pins
├── inventories/
│   ├── production/
│   │   ├── hosts.yml
│   │   ├── group_vars/
│   │   └── host_vars/
│   ├── staging/
│   └── development/
├── playbooks/
│   ├── site.yml              # full stack
│   ├── webservers.yml        # slice
│   └── deploy-app.yml
├── roles/
│   ├── common/
│   ├── nginx/
│   └── app/
├── collections/
├── filter_plugins/
├── .ansible-lint
├── .yamllint.yml
├── molecule/                 # per-role tests
└── .github/workflows/ansible.yml
```

Principles:

- **One repo** or mono-repo path per team — avoid copy-paste playbooks.
- **Separate inventory per environment** — never share `group_vars/all` secrets across prod/stage without intent.
- **Pin everything** in `requirements.yml`.
- **Small playbooks** — `site.yml` imports focused playbooks.

```yaml
# playbooks/site.yml
---
- import_playbook: webservers.yml
- import_playbook: deploy-app.yml
```

---

## 2. ansible-lint

Catches deprecated syntax, risky modules, and style issues.

```bash
pip install ansible-lint
cd ansible/day7/labs
ansible-lint playbooks/site.yml
ansible-lint roles/
```

`.ansible-lint`:

```yaml
---
profile: production
exclude_paths:
  - .cache/
  - molecule/
skip_list:
  - yaml[line-length]
```

Run in CI on every PR — fail build on severity `error`.

---

## 3. Molecule (testing roles)

Molecule provisions ephemeral instances (Docker, cloud), applies role, verifies with **testinfra** or Ansible `assert`.

```bash
cd roles/nginx
molecule init scenario -d docker
molecule test    # create, converge, verify, destroy
```

Minimal `molecule/default/verify.yml`:

```yaml
---
- name: Verify nginx
  hosts: all
  gather_facts: false
  tasks:
    - name: Check nginx listening
      ansible.builtin.wait_for:
        port: 80
        timeout: 5

    - name: HTTP check
      ansible.builtin.uri:
        url: http://localhost/
        status_code: 200
```

**DevOps value:** Same role tested in CI before anyone runs against production.

---

## 4. AWX / Ansible Automation Platform

| Feature | Purpose |
|---------|---------|
| Job templates | Run playbooks with RBAC |
| Credentials | Vault, SSH, cloud — not in job logs |
| Schedules | Compliance scans nightly |
| Workflow | Chain job templates (provision → configure → test) |
| Surveys | Prompt variables at runtime |
| Inventory sources | Sync from cloud every N minutes |

Flow:

```
Git push → CI lint/test → AWX webhook → Job template (staging) → Manual approval → Production
```

For small teams, **CI-only** (GitHub Actions) without AWX is fine — same playbooks, different runner.

---

## 5. CI/CD: GitHub Actions example

```yaml
name: Ansible CI

on:
  pull_request:
    paths: ['ansible/**']
  push:
    branches: [main]

jobs:
  lint-and-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Ansible tooling
        run: |
          pip install ansible ansible-lint
          ansible-galaxy collection install -r ansible/day7/labs/requirements.yml

      - name: Ansible Lint
        run: ansible-lint ansible/day7/labs/playbooks/site.yml

      - name: Syntax check
        run: |
          cd ansible/day7/labs
          ansible-playbook playbooks/site.yml --syntax-check

      - name: Dry-run (check mode) against lab
        if: github.event_name == 'push'
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
        run: |
          cd ansible/day7/labs
          echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vp
          chmod 600 /tmp/vp
          ansible-playbook playbooks/site.yml \
            -i inventory/staging/ \
            --check --diff \
            --vault-password-file /tmp/vp
          rm -f /tmp/vp
```

**Secrets:** Vault password, SSH keys, cloud creds in platform secret store — never in repo.

---

## 6. Operational best practices

| Practice | Why |
|----------|-----|
| Idempotent playbooks | Safe to re-run; fixes drift |
| `--check` in CI | Catch unintended changes before apply |
| `--diff` in CI | Reviewable file changes in logs |
| `serial` + health checks | Zero-downtime deploys |
| Tags | Fast app-only deploys |
| Version pins | Reproducible runs |
| Least privilege become | Dedicated sudoers per role |
| Logging | AWX job output or CI artifacts retained |
| `--limit` for canary | One host first, then fleet |

### Terraform + Ansible boundary

| Terraform | Ansible |
|-----------|---------|
| Networks, VMs, LB, IAM | OS packages, config files, app deploy |
| State file | Facts + inventory |
| `terraform apply` | `ansible-playbook site.yml` |

Run order: **Terraform → Ansible → smoke tests**.

---

## 7. Performance at scale

- `strategy: free` for independent hosts (watch load on control node).
- `forks` tuning in `ansible.cfg`.
- `pipelining = True` for SSH.
- `gather_facts: false` when not needed; cache facts otherwise.
- **Mitogen** (third-party) — faster connection setup on huge fleets.
- Split large playbooks; use `import_playbook` for parallelism at workflow level.

---

## 8. Security checklist

- [ ] Vault or external secret manager for credentials
- [ ] `host_key_checking = True` in production
- [ ] No `ignore_errors` on security tasks without alerting
- [ ] Audit Galaxy roles before use
- [ ] `no_log: true` on tasks that register secrets
- [ ] RBAC on AWX / CI deploy keys
- [ ] Signed commits on playbook repo

```yaml
- name: Set DB password
  ansible.builtin.user:
    name: app
    password: "{{ db_password | password_hash('sha512') }}"
  no_log: true
```

---

## 9. Capstone lab — Day 7

From `ansible/day7/labs/` — **Handbook Web Stack**:

**Architecture:**

```
┌─────────────┐     ┌─────────────┐
│  web1       │     │  web2       │
│  nginx      │     │  nginx      │
│  app vX     │     │  app vX     │
└─────────────┘     └─────────────┘
        │                   │
        └─────────┬─────────┘
                  │
           (optional db1)
```

**Tasks:**

1. Review production layout under `labs/` — `inventories/staging`, `playbooks/site.yml`, three roles.
2. `ansible-galaxy collection install -r requirements.yml`
3. Create vault: `ansible-vault create inventories/staging/group_vars/webservers/vault.yml` with `vault_app_secret`.
4. `ansible-lint .` — fix any reported issues.
5. `ansible-playbook playbooks/site.yml -i inventories/staging/ --syntax-check`
6. `ansible-playbook playbooks/site.yml -i inventories/staging/ --check --diff --vault-password-file ...`
7. Apply for real; verify HTTP on both web servers.
8. Bump `app_version` in `group_vars/webservers.yml`; run with `--tags deploy` only.
9. Document rollback procedure (previous `app_version` + re-run playbook).
10. Optional: add GitHub Actions workflow from section 5 to your fork.

**Deliverable:** Short `CAPSTONE.md` in your notes: inventory source, how secrets are managed, how you would add a third environment.

---

## 10. Where to go next

| Topic | Resource |
|-------|----------|
| AWX | [ansible.com/automation](https://www.ansible.com/products/automation-platform) |
| Molecule | [ansible.readthedocs.io/projects/molecule](https://ansible.readthedocs.io/projects/molecule/) |
| Collections index | [docs.ansible.com/collections](https://docs.ansible.com/ansible/latest/collections/index.html) |
| Red Hat certification | RHCE (EX294) — Ansible focus |

Related handbooks: [Kubernetes](../kubernetes/README.md) (`kubernetes.core`), [AWS](../aws/README.md) (`amazon.aws`).

---

## Quick reference

| Task | Command |
|------|---------|
| Lint | `ansible-lint playbooks/site.yml` |
| Molecule test | `cd roles/x && molecule test` |
| Staging deploy | `ansible-playbook site.yml -i inventories/staging/` |
| App-only | `ansible-playbook site.yml --tags deploy` |

**Previous:** [Day 6 — Dynamic inventory](../day6/)

---

## Handbook completion

You now have a path from ad-hoc commands to production automation. Revisit days with real infrastructure, pin collections, and wire CI — that is where professional Ansible practice lives.
