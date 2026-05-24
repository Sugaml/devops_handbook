# Day 13 — Environment Variables, python-dotenv & Secrets Hygiene

**Goal:** Load configuration from environment variables safely, use `.env` files correctly in development, and apply secrets hygiene patterns that prevent credential leaks in DevOps automation.

**Time:** 4–5 hours (theory + hands-on)

---

## 1. The 12-factor config rule

**Config belongs in the environment**, not in code or committed files. DevOps scripts read:

```
  OS env vars  ──►  application / script
       ▲
  CI secrets, K8s Secrets, IAM roles
```

| Source | When to use |
|--------|-------------|
| Shell `export` | Local dev, ad-hoc scripts |
| `.env` file (gitignored) | Local dev convenience only |
| CI secret store | GitHub Secrets, GitLab CI variables |
| Runtime injection | Kubernetes `envFrom`, ECS task defs |

---

## 2. os.environ and os.getenv

Standard library — no dependencies:

```python
import os

def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable not set: {name}")
    return value

region = os.getenv("AWS_REGION", "us-east-1")  # default for optional vars
db_url = require_env("DATABASE_URL")
```

Use `os.environ` when you want KeyError on missing keys; `getenv` when defaults are intentional.

---

## 3. python-dotenv for local development

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (never commit this file)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

api_key = require_env("API_KEY")
```

**Critical rules:**

1. Add `.env` to `.gitignore` — always.
2. Commit `.env.example` with **placeholder** values only.
3. In production/CI, inject real values via the platform — do **not** ship `.env` files.
4. Call `load_dotenv()` once at startup, early in `main()`.

```bash
# .env.example — safe to commit
API_KEY=replace-me
DATABASE_URL=postgresql://user:pass@localhost:5432/app
LOG_LEVEL=info
```

---

## 4. Typed settings with dataclasses

```python
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    api_key: str
    database_url: str
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            api_key=require_env("API_KEY"),
            database_url=require_env("DATABASE_URL"),
            log_level=os.getenv("LOG_LEVEL", "info"),
        )
```

Immutable settings objects prevent accidental mutation mid-run and make testing easy (inject fake `Settings`).

---

## 5. Secrets hygiene — non-negotiables

| Do | Don't |
|----|-------|
| Use the platform injects at runtime | Hard-code keys in `.py` files |
| Rotate keys; use short-lived tokens | Log full env dumps in CI |
| Redact secrets in error messages | `print(os.environ)` in production |
| Use IAM roles / OIDC over static keys | Commit `.env` with real credentials |
| Scan repos with gitleaks/trufflehog | Share secrets in Slack/email |

```python
def redact(value: str, visible: int = 4) -> str:
    if len(value) <= visible:
        return "****"
    return value[:visible] + "****"

# Safe logging
print(f"Using API key {redact(api_key)}")
```

---

## 6. Detecting accidental secret exposure

```python
SENSITIVE_KEYS = ("password", "secret", "token", "key", "credential")

def audit_environ() -> list[str]:
    warnings = []
    for name in os.environ:
        lower = name.lower()
        if any(s in lower for s in SENSITIVE_KEYS):
            if len(os.environ[name]) > 0:
                warnings.append(f"{name} is set ({redact(os.environ[name])})")
    return warnings
```

Run audits in CI pre-flight: confirm required vars exist, flag unexpected secret-like vars in logs.

---

## 7. Priority: env over file over default

Production pattern:

```python
def get_config_value(key: str, default: str | None = None) -> str | None:
    # 1. Environment always wins
    if key in os.environ:
        return os.environ[key]
    return default
```

Never let a `.env` file override CI-injected secrets — load order matters:

```python
# Correct: .env fills gaps; existing env vars are preserved
load_dotenv(override=False)
```

---

## 8. Kubernetes and Docker equivalents

| Platform | Mechanism |
|----------|-----------|
| Docker | `-e VAR=val`, `--env-file .env` (dev), Docker secrets |
| Kubernetes | `env`, `envFrom`, External Secrets Operator |
| AWS ECS | Task definition `secrets` from Secrets Manager |
| GitHub Actions | `${{ secrets.MY_TOKEN }}` |

Your Python code stays the same — only the injection layer changes.

---

## 9. Lab — Day 13

Work from `python/day13/labs/`.

1. Copy `.env.example` to `.env` and fill in fake values.
2. Run `python env_loader.py` — prints loaded settings with redacted secrets.
3. Unset `API_KEY` and run again — confirm clear error message, exit code 1.
4. Run `python env_loader.py --audit` — lists sensitive env vars without exposing values.
5. Set `load_dotenv(override=True)` temporarily and export a different `LOG_LEVEL` in shell — observe override behavior; restore `override=False`.
6. Add a deliberate "secret" to a dummy log line; run `--check-logs` scanner on sample log file.

**Stretch:** Integrate with Day 11 config loader — env vars override YAML defaults.

---

## 10. DevOps connections

- **CI/CD:** Pipeline variables map 1:1 to `os.environ` in Python deploy scripts.
- **Terraform:** Never pass secrets via `-var`; use env vars (`TF_VAR_`) or secret stores.
- **Incident response:** Leaked `.env` in git history requires rotation + history rewrite — prevention beats cleanup.

---

## Quick reference

| Task | Code |
|------|------|
| Read env var | `os.getenv("KEY", "default")` |
| Require env var | `os.environ["KEY"]` or custom `require_env` |
| Load .env (dev) | `load_dotenv(override=False)` |
| Redact for logs | Show first 4 chars + `****` |
| Never commit | `.env` in `.gitignore`, `.env.example` committed |

**Next:** [Day 14 — datetime, timezones & scheduling patterns](../day14/)
