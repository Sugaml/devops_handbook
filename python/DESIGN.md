# Python Handbook — Design & curriculum notes

## Goals

- **Terminal-first**: Every day is actionable from a shell; IDE optional.
- **DevOps trajectory**: Language basics → ops scripting → cloud/infra SDKs → quality & packaging → security → capstone.
- **Runnable labs**: Each day ships at least one script you can execute; Day 30 is a multi-module package.
- **Bridge to other handbooks**: Python complements Ansible, AWS CLI, Terraform, Kubernetes, and CI/CD tracks in this repo.

## Pedagogy

| Pattern | Usage |
|---------|--------|
| Goal + time box | Sets expectations (3–8 h/day) |
| Tables | Type comparison, CLI flags, SDK methods |
| Code blocks | Runnable commands and Python |
| DevOps callout | CI, least privilege, dry-run, observability |
| Lab | Creates + verifies + optional stretch |
| Prev/Next links | Linear path; skip ahead only with prerequisites met |

## Curriculum arc

```
Days 1–7   Language + packaging foundation
Days 8–14  CLI scripts, configs, HTTP, env/secrets
Days 15–21 Cloud, containers, K8s, SSH, Git, DB, Ansible
Days 22–28 Testing, types, CLIs, APIs, logs, async, Poetry
Days 29–30 Security scanning + incident toolkit capstone
```

## Design decisions

| Decision | Rationale |
|----------|-----------|
| `python3` everywhere | Avoids Python 2 ambiguity on legacy systems |
| argparse before Click/Typer | Stdlib first; advanced CLIs on Day 24 |
| subprocess before SDKs | Understand shell escape hatches before abstractions |
| boto3 as primary cloud SDK | Matches [AWS handbook](../aws/README.md); patterns transfer to Azure/GCP |
| Pydantic v2 on Day 23+ | Industry standard for config validation in ops tools |
| Poetry on Day 28 | Modern packaging; pip + pyproject still covered Day 7 |
| Capstone CLI + optional API | Mirrors real on-call tools (CLI for speed, API for dashboards) |

## Edge cases documented in days

- **Shebang + venv**: `#!/usr/bin/env python3` vs absolute venv path (Day 1, 7).
- **Shell injection**: Never `shell=True` with user input; use list args (Day 9).
- **Secrets in logs**: Redact env vars and tokens (Day 6, 13, 29).
- **AWS credentials**: Profile/env/role chain; no keys in code (Day 13, 15).
- **K8s kubeconfig**: Context switching and in-cluster vs local (Day 17).
- **SSH host keys**: `AutoAddPolicy` lab-only; production uses known_hosts (Day 18).
- **Async vs threads**: I/O-bound health checks → asyncio (Day 27).
- **Check mode / dry-run**: Ansible and destructive boto3 calls (Day 21, 15).

## Performance / safety optimizations

- **Connection pooling**: `requests.Session`, boto3 client reuse (Days 12, 15).
- **Concurrent checks**: asyncio + semaphore limits (Day 27).
- **Structured JSON logs**: machine-parseable incident trails (Day 26, 30).
- **Exit codes**: CI-friendly scripts return non-zero on failure (Days 8+).
- **pytest mocks**: Avoid live cloud in unit tests (Day 22).

## Capstone (Day 30) integration map

| Prior day | Used in capstone |
|-----------|------------------|
| 21 | Dynamic inventory, Ansible subprocess |
| 22 | pytest suite |
| 23 | Pydantic models for config |
| 24 | Typer CLI |
| 25 | Optional FastAPI sidecar |
| 26 | structlog-style logging, Prometheus |
| 27 | Async health assessment |
| 28 | Poetry project layout |
| 29 | Security patterns (no secrets in repo) |

## User feedback / iteration

- Add **Azure SDK** / **google-cloud** parallel labs if requested (Day 15 pattern).
- Optional **Terraform CDK for Python** day (cross-link terraform handbook).
- Expand **Windows ops** track (WinRM, pywin32) for hybrid shops.
- **Jupyter notebooks** for log analysis — optional appendix.

## Versioning

- Written for Python 3.10–3.12 and common PyPI packages as of 2025–2026.
- Pin versions in lab `requirements.txt` / `pyproject.toml` when teaching reproducibility (Day 28, 29).
