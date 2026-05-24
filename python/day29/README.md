# Day 29 — Security: bandit, pip-audit & Secret Scanning in CI

**Goal:** Integrate static analysis, dependency vulnerability scanning, and secret detection into Python CI pipelines — fail builds on critical findings before code reaches production.

**Time:** 4–5 hours

**Prerequisites:** Day 22 (pytest in CI); Day 28 (Poetry lock files)

---

## 1. DevOps security shift-left

Python ops tools often have:

- Broad cloud IAM credentials
- SSH keys and API tokens in env vars
- Shell injection in subprocess wrappers
- Unpinned dependencies with known CVEs

Shift-left means catching these in PR checks, not during an incident.

| Layer | Tool | Finds |
|-------|------|-------|
| SAST | **bandit** | `subprocess` shell=True, weak crypto, hardcoded passwords |
| Dependencies | **pip-audit** | Known CVEs in installed packages |
| Secrets | **gitleaks**, **trufflehog** | Committed tokens, keys |
| Lint | **ruff** | Some security antipatterns |

---

## 2. bandit — Python SAST

```bash
pip install bandit[toml]
bandit -r python/day29/labs -c pyproject.toml
```

Configure in `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests", ".venv"]
skips = ["B101"]  # assert_used — OK in tests only if not excluded from scan path
```

Common findings in infra code:

| ID | Issue | Fix |
|----|-------|-----|
| B602 | `subprocess` with `shell=True` | Use list args, no shell |
| B105 | Hardcoded password string | Move to env / secret manager |
| B608 | SQL injection | Parameterized queries |
| B301 | pickle | Never unpickle untrusted data |

See `labs/insecure_examples.py` — intentionally vulnerable for lab scans.

---

## 3. pip-audit — dependency CVEs

```bash
pip install pip-audit
pip-audit -r requirements.txt
# or with Poetry:
poetry export -f requirements.txt --without-hashes -o /tmp/requirements.txt
pip-audit -r /tmp/requirements.txt
```

Interpret output:

```
Found 2 known vulnerabilities in 1 package
Name    Version  ID                  Fix Versions
flask   2.0.0    PYSEC-2023-xxx      2.3.2
```

**Policy:** Fail CI on `CRITICAL` and `HIGH`; warn on `MEDIUM`; track exceptions with ticket IDs.

```bash
pip-audit -r requirements.txt --strict --desc on
```

---

## 4. Secret scanning

### gitleaks (repo-wide)

```bash
brew install gitleaks
gitleaks detect --source . --verbose
```

### pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml", "-r", "python/day29/labs"]
```

### Custom Python guard (defense in depth)

`labs/scan_secrets.py` scans staged files for high-entropy strings and known patterns before commit.

---

## 5. CI workflow integration

See `labs/.github/workflows/security.yml`:

```yaml
name: python-security
on: [pull_request, push]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install bandit pip-audit
      - run: bandit -r python/day29/labs -ll -c python/day29/labs/pyproject.toml
      - run: pip-audit -r python/day29/labs/requirements.txt
      - uses: gitleaks/gitleaks-action@v2
```

Order: **lint → unit tests → bandit → pip-audit → gitleaks** for fast feedback.

---

## 6. Handling false positives

Document suppressions with justification:

```python
subprocess.call("ls", shell=True)  # nosec B602 — lab example only
```

```toml
# bandit baseline for legacy code
[tool.bandit.assert_used]
skips = ["*/tests/*"]
```

Prefer fixing code over permanent `# nosec` comments.

---

## 7. Supply chain hardening

- Pin hashes in requirements (`pip install --require-hashes`)
- Use private PyPI mirror with vulnerability scanning
- Enable Dependabot/Renovate on internal packages
- Sign wheels (Sigstore) for high-assurance environments

---

## 8. Lab — Day 29

Work from `python/day29/labs/`.

1. Run `bandit -r . -c pyproject.toml` — note findings in `insecure_examples.py`.
2. Fix one issue (remove hardcoded password); re-run until that finding clears.
3. Run `pip-audit -r requirements.txt` — review any CVEs (lab uses minimal deps).
4. Run `python scan_secrets.py` against the labs directory.
5. Copy `insecure_examples.py` to `insecure_examples_fixed.py` and remediate all bandit HIGH findings.
6. Review `.github/workflows/security.yml` — identify where you'd add pytest.
7. **Stretch:** Add bandit to pre-commit and run on staged files only.

**Success criteria:** You can explain each bandit finding; CI workflow runs three security tools.

---

## 9. DevOps connections

- **SOC2 / ISO audits:** CI logs prove every merge was scanned.
- **Incident prevention:** Catching AWS keys in git beats rotating them at 3 AM.
- **Platform trust:** Internal CLIs with broad permissions demand the strictest scans.

---

## Quick reference

| Task | Command |
|------|---------|
| bandit scan | `bandit -r . -c pyproject.toml` |
| High severity only | `bandit -r . -ll` |
| pip-audit | `pip-audit -r requirements.txt` |
| gitleaks | `gitleaks detect --source .` |
| Local secret scan | `python scan_secrets.py path/` |

**Next:** [Day 30 — Capstone incident response toolkit](../day30/)
