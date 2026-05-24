# Python for DevOps — 30-Day Handbook

A hands-on path from your first `python3` script to production-grade automation: cloud SDKs, Kubernetes, testing, observability, security scanning, and a capstone incident response toolkit. Each day combines **concepts**, **copy-paste examples**, and a **runnable lab**.

## Structure

### Week 1 — Python fundamentals

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Setup, REPL, variables, types, f-strings | [day1](./day1/) |
| 2 | Control flow (if/for/while), truthiness, enumerate | [day2](./day2/) |
| 3 | Functions, docstrings, scope, *args/**kwargs | [day3](./day3/) |
| 4 | Lists, dicts, sets, comprehensions, parsing data | [day4](./day4/) |
| 5 | Strings, files, pathlib, reading logs | [day5](./day5/) |
| 6 | Exceptions, try/except/finally, logging | [day6](./day6/) |
| 7 | Modules, packages, venv, pip, pyproject.toml | [day7](./day7/) |

### Week 2 — Scripting for operators

| Day | Topic | Folder |
|-----|--------|--------|
| 8 | argparse CLI design for ops scripts | [day8](./day8/) |
| 9 | subprocess — shell commands safely | [day9](./day9/) |
| 10 | os, sys, pathlib, permissions, glob | [day10](./day10/) |
| 11 | JSON, YAML, TOML config loading | [day11](./day11/) |
| 12 | HTTP with requests — API health checks | [day12](./day12/) |
| 13 | Environment variables, dotenv, secrets hygiene | [day13](./day13/) |
| 14 | datetime, timezones, scheduling patterns | [day14](./day14/) |

### Week 3 — Infrastructure automation

| Day | Topic | Folder |
|-----|--------|--------|
| 15 | boto3 — EC2, S3, STS inventory | [day15](./day15/) |
| 16 | Docker automation (SDK & subprocess) | [day16](./day16/) |
| 17 | Kubernetes client-python | [day17](./day17/) |
| 18 | SSH automation with Paramiko | [day18](./day18/) |
| 19 | Git automation with GitPython | [day19](./day19/) |
| 20 | Database health checks (SQLite / PostgreSQL) | [day20](./day20/) |

### Week 4 — Quality, APIs & concurrency

| Day | Topic | Folder |
|-----|--------|--------|
| 21 | Ansible programmatic use, dynamic inventory | [day21](./day21/) |
| 22 | pytest — testing infrastructure code | [day22](./day22/) |
| 23 | Type hints, Pydantic validation, mypy | [day23](./day23/) |
| 24 | Click / Typer advanced CLIs | [day24](./day24/) |
| 25 | FastAPI for internal ops tools | [day25](./day25/) |
| 26 | Structured logging & Prometheus metrics | [day26](./day26/) |
| 27 | asyncio & aiohttp concurrent health checks | [day27](./day27/) |
| 28 | Packaging with Poetry, distributing tools | [day28](./day28/) |

### Week 5 — Security & production capstone

| Day | Topic | Folder |
|-----|--------|--------|
| 29 | Security — bandit, pip-audit, secret scanning | [day29](./day29/) |
| 30 | Capstone — incident response toolkit | [day30](./day30/) |

## Prerequisites

- Comfort with a terminal ([Linux handbook](../linux/README.md) Days 1–5 recommended).
- Python **3.10+** on your laptop or lab VM.
- No prior Python required; shell scripting experience helps.
- For Days 15–21: optional cloud/K8s/Docker lab environments (links in each day).
- For Day 21: [Ansible handbook](../ansible/README.md) Day 1–2 recommended.

## How to use this handbook

1. Complete **Day 1** setup and verify `python3 --version` before anything else.
2. Work from `python/dayN/labs/`; run scripts with `python3 labs/script.py`.
3. Use a virtual environment from **Day 7** onward (`python3 -m venv .venv && source .venv/bin/activate`).
4. Finish each day's **Lab** section before advancing.
5. Keep a personal cheat sheet of patterns you reuse at work (argparse, boto3, pytest fixtures).

## Recommended lab setup

```bash
# macOS
brew install python@3.12
python3 --version

# Ubuntu / Debian
sudo apt update && sudo apt install -y python3 python3-venv python3-pip

# Project venv (use per-day or one handbook venv)
cd python
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Core deps for later weeks (install as needed per day)
pip install pyyaml requests httpx python-dotenv boto3 docker kubernetes \
  paramiko gitpython psycopg2-binary pytest pydantic typer fastapi \
  prometheus-client aiohttp bandit pip-audit poetry
```

## Project conventions

| Convention | Value |
|------------|--------|
| Interpreter | `python3` |
| Style | `snake_case`, type hints where natural |
| Examples | Hosts, logs, deploys, configs, health checks |
| Exit codes | `0` success, `1` failure, `2` usage error (CLIs) |
| Output | JSON for machine-readable ops scripts |

Sample labs live under each day's `labs/` folder. Day 30 combines them into `labs/incident_toolkit/`.

## Design notes

- **Python 3.10+** — uses `match` sparingly; `tomllib` stdlib on 3.11+.
- **DevOps trajectory:** Days 1–7 (language) → 8–14 (scripting) → 15–21 (infra) → 22–28 (quality) → 29–30 (security + capstone).
- **Idempotency & safety:** prefer dry-run flags, `--check`, and explicit confirmation for destructive ops.
- Cross-links to [AWS](../aws/README.md), [Ansible](../ansible/README.md), [Kubernetes](../kubernetes/README.md), and [Docker](../docker/README.md) handbooks where relevant.

See [DESIGN.md](./DESIGN.md) for curriculum rationale, edge cases, and iteration notes.

## Progress checklist

```
Week 1:  [ ] Day 1  [ ] Day 2  [ ] Day 3  [ ] Day 4  [ ] Day 5  [ ] Day 6  [ ] Day 7
Week 2:  [ ] Day 8  [ ] Day 9  [ ] Day 10 [ ] Day 11 [ ] Day 12 [ ] Day 13 [ ] Day 14
Week 3:  [ ] Day 15 [ ] Day 16 [ ] Day 17 [ ] Day 18 [ ] Day 19 [ ] Day 20
Week 4:  [ ] Day 21 [ ] Day 22 [ ] Day 23 [ ] Day 24 [ ] Day 25 [ ] Day 26 [ ] Day 27 [ ] Day 28
Week 5:  [ ] Day 29 [ ] Day 30 — capstone
```

**Start here:** [Day 1 — Setup, REPL & First Script](./day1/)
