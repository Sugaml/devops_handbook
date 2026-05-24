# Day 30 — Capstone: Incident Response Toolkit

**Goal:** Build a production-style **incident response toolkit** that combines Ansible orchestration, async health checks, structured logging, Prometheus metrics, typed config, CLI, optional API, and tests — the synthesis of Days 21–29.

**Time:** 6–8 hours

**Prerequisites:** Days 21–29; Ansible optional for live playbook runs

---

## 1. Capstone scenario

It's 2:14 AM. PagerDuty fires **"Elevated 5xx on staging web tier."** You need to:

1. **Assess** — concurrent health checks across all registered endpoints
2. **Inventory** — know which hosts exist and their groups
3. **Remediate** — run an approved Ansible ping or restart playbook (dry-run first)
4. **Report** — JSON summary for Slack and metrics for the war room dashboard
5. **Audit** — structured logs with incident ID on every action

The `incident_toolkit` package implements this workflow as a Typer CLI and optional FastAPI sidecar.

---

## 2. Architecture

```
                    ┌─────────────────────────────────────┐
                    │           incident CLI              │
                    │  assess │ inventory │ remediate     │
                    └──────────┬──────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
   ┌───────────┐        ┌────────────┐       ┌─────────────┐
   │  health   │        │ inventory  │       │ ansible_ops │
   │ (async)   │        │ (dynamic)  │       │ (subprocess)│
   └───────────┘        └────────────┘       └─────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ models + config     │
                    │ (Pydantic v2)       │
                    └─────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
       ┌─────────────┐                   ┌─────────────┐
       │ logging     │                   │ metrics     │
       │ (structlog) │                   │ (prometheus)│
       └─────────────┘                   └─────────────┘
```

Optional: `incident-api` serves `/health`, `/metrics`, and `POST /incidents/assess`.

---

## 3. Project layout

```
python/day30/labs/incident_toolkit/
├── pyproject.toml
├── targets.example.yaml
├── hosts_registry.json
├── src/incident_toolkit/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── inventory.py
│   ├── health.py
│   ├── ansible_ops.py
│   ├── logging_setup.py
│   ├── metrics.py
│   └── api.py
└── tests/
    ├── conftest.py
    ├── test_health.py
    ├── test_models.py
    └── test_cli.py
```

Install:

```bash
cd python/day30/labs/incident_toolkit
poetry install
poetry run incident --help
```

---

## 4. Typed incident configuration

`models.py` defines the contract:

```python
class IncidentContext(BaseModel):
    incident_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    severity: Literal["sev1", "sev2", "sev3"] = "sev2"
    environment: Literal["dev", "staging", "prod"]
    dry_run: bool = True

class AssessResult(BaseModel):
    incident_id: str
    summary: HealthSummary
    unhealthy: list[CheckResult]
```

Every CLI command binds `incident_id` into structlog context for correlation.

---

## 5. Module responsibilities

| Module | Responsibility |
|--------|----------------|
| `inventory.py` | Load host registry JSON; build Ansible-style groups |
| `health.py` | Async concurrent probes (Day 27) |
| `ansible_ops.py` | Run playbooks with dry-run guard (Day 21) |
| `logging_setup.py` | JSON structured logs (Day 26) |
| `metrics.py` | Counters for assess/remediate actions |
| `cli.py` | Typer commands: assess, inventory, remediate, serve-api |
| `api.py` | FastAPI endpoints for dashboards (Day 25) |

---

## 6. CLI commands

```bash
# Full incident assessment
poetry run incident assess targets.example.yaml --env staging --json

# Show dynamic inventory
poetry run incident inventory --json

# Remediate (dry-run default — safe)
poetry run incident remediate --playbook playbooks/ping.yml --dry-run

# Live run (requires explicit flag)
poetry run incident remediate --playbook playbooks/ping.yml --no-dry-run

# Start API + metrics on :8080
poetry run incident serve-api --port 8080
```

Global flags: `--verbose`, `--incident-id` (for continuing an existing incident).

---

## 7. Assessment workflow

```python
async def assess_targets(targets, concurrency=30) -> AssessResult:
    results = await run_checks(targets, concurrency=concurrency)
    unhealthy = [r for r in results if not r.ok]
    INCIDENT_ASSESS_TOTAL.labels(status="unhealthy" if unhealthy else "healthy").inc()
    return AssessResult(...)
```

CLI prints human summary or JSON for ChatOps bot ingestion.

---

## 8. Remediation guardrails

Production safety defaults:

1. **`dry_run=True`** unless `--no-dry-run` passed
2. **`--limit`** host pattern required for prod environment
3. Playbook path must be under approved directory
4. All actions logged with `incident_id`, `operator`, `playbook`

```python
def run_playbook(..., dry_run: bool = True) -> PlaybookResult:
    cmd = ["ansible-playbook", playbook, "-i", inventory]
    if dry_run:
        cmd.append("--check")
    log.info("ansible_playbook_start", cmd=cmd, dry_run=dry_run)
    ...
```

---

## 9. Observability during incidents

Metrics exposed at `/metrics`:

- `incident_assess_total{status=}`
- `incident_remediate_total{status=}`
- `incident_check_duration_seconds`

Logs (JSON):

```json
{"event": "assess_complete", "incident_id": "a1b2c3d4", "unhealthy": 2, "level": "warning"}
```

Wire Grafana panels to `rate(incident_assess_total{status="unhealthy"}[5m])`.

---

## 10. Testing strategy

```bash
poetry run pytest -v
poetry run mypy src
```

Tests mock aiohttp and subprocess — no live Ansible required in CI. Integration tests marked `@pytest.mark.integration`.

---

## 11. Lab — Day 30

Work from `python/day30/labs/incident_toolkit/`.

1. `poetry install` and `poetry run incident --help`.
2. Run assessment: `poetry run incident assess targets.example.yaml --json | jq .summary`.
3. List inventory: `poetry run incident inventory`.
4. Dry-run remediation: `poetry run incident remediate --playbook ../../day21/labs/playbooks/ping.yml`.
5. Start API: `poetry run incident serve-api` — curl `/health` and `/metrics`.
6. Run full test suite: `poetry run pytest -v`.
7. Simulate incident: set `LOG_FORMAT=json`, run assess with `--incident-id drill-001`, grep logs for `incident_id`.
8. **Stretch:** Wire a Slack webhook POST on assess with unhealthy count > 0.

**Success criteria:** CLI assess returns JSON summary; tests pass; metrics increment; logs include incident_id.

---

## 12. DevOps connections

- **Runbooks:** Replace ad-hoc bash with `incident assess` as step 1 of every outage runbook.
- **ChatOps:** `/incident assess staging` bot calls the FastAPI endpoint.
- **Post-incident review:** JSON logs filtered by `incident_id` produce a timeline.
- **Platform maturity:** Package and publish via Poetry (Day 28) to your internal PyPI.

---

## Quick reference

| Task | Command |
|------|---------|
| Install | `poetry install` |
| Assess fleet | `poetry run incident assess targets.yaml --json` |
| Inventory | `poetry run incident inventory` |
| Dry-run fix | `poetry run incident remediate --playbook path.yml` |
| API mode | `poetry run incident serve-api --port 8080` |
| Tests | `poetry run pytest -v` |

**Congratulations** — you've completed the Python for DevOps handbook (Days 21–30). Review earlier days for fundamentals and revisit this capstone to extend with your organization's real playbooks and service registry.
