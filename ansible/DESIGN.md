# Ansible Handbook — Design & curriculum notes

## Goals

- **CLI-first**: Every day is actionable from a terminal; AWX/AAP introduced on Day 7 as the enterprise UI layer.
- **DevOps trajectory**: Days 1–2 (inventory + playbooks) → 3–4 (data + reuse) → 5–6 (secrets + scale) → 7 (testing + CI/CD capstone).
- **Idempotency throughout**: Labs verify "second run = 0 changes" where possible.

## Pedagogy

| Pattern | Usage |
|---------|--------|
| Goal + time box | Sets expectations (3–6 h/day) |
| Tables | Module comparison, directory layouts |
| Code blocks | Runnable commands and YAML |
| DevOps callout | CI, least privilege, drift detection |
| Lab | Creates + verifies + optional teardown |
| Prev/Next links | Linear path with optional skips |

## Edge cases documented in days

- **SSH host key checking**: Disabled in lab `ansible.cfg` only — production uses known_hosts or `ansible_ssh_common_args`.
- **Python interpreter discovery**: `ansible_python_interpreter` on minimal images (Day 1, 6).
- **Become/sudo**: Password vs key; `--ask-become-pass` vs passwordless sudo in `/etc/sudoers.d/`.
- **Check mode limitations**: Not all modules support `--check`; `check_mode: yes` in module docs (Day 2, 5).
- **Fact caching**: Performance vs staleness (Day 6).
- **Vault in CI**: `--vault-password-file` from secret store, never committed (Day 5, 7).

## Performance / safety optimizations

- **Mitogen** / **free strategy** mentioned for large fleets (Day 5) — default `linear` for learning.
- **Fact gathering**: `gather_facts: false` when facts unused (Day 3, 7).
- **Serial** rolling updates for zero-downtime deploys (Day 5).
- **ansible-lint** and **molecule** in Day 7 — catch anti-patterns before merge.

## User feedback / iteration

- Add Windows WinRM track if requested (parallel to Day 2–4).
- Optional **Terraform + Ansible** companion: Terraform provisions, Ansible configures (Day 7 seeds this).
- Expand cloud dynamic inventory labs per cloud handbook (AWS `amazon.aws`, Azure `azure.azcollection`).

## Versioning

- Written for Ansible Core 2.15–2.16 and `ansible-lint` 6.x as of 2025–2026.
- Collection versions pinned in Day 7 `requirements.yml` example.
