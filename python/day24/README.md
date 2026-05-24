# Day 24 — Advanced CLIs with Click & Typer

**Goal:** Build production-grade operator CLIs — subcommands, global options, env/config precedence, rich output, and exit codes suitable for CI and on-call use.

**Time:** 4–5 hours

**Prerequisites:** Days 1–20 Python basics; Day 23 (typed config) recommended

---

## 1. CLI design for operators

Good ops CLIs are:

- **Predictable** — `--help` on every subcommand; consistent flag names
- **Scriptable** — meaningful exit codes; `--json` for automation
- **Safe** — `--dry-run` / `--confirm` for destructive actions
- **Fast** — lazy imports so `--help` doesn't load boto3

| Shell script wrapper | Python CLI (Click/Typer) |
|----------------------|--------------------------|
| Fragile argument parsing | Typed parameters, validation |
| Inconsistent `--help` | Auto-generated from signatures |
| Hard to test | Invoke runner in pytest |

---

## 2. Click vs Typer

| Feature | Click | Typer |
|---------|-------|-------|
| Style | Decorator-based | Type hints → CLI |
| Best for | Complex custom behavior | Fast development |
| Testing | `CliRunner` | Same (Typer uses Click) |
| Shell completion | Built-in | Built-in |

This lab uses **Typer** for the main tool and shows equivalent **Click** patterns in theory sections.

---

## 3. Project structure

```
python/day24/labs/
├── ops_cli.py          # Typer entrypoint
├── config.py           # settings + context
└── commands/
    ├── __init__.py
    ├── hosts.py
    └── deploy.py
```

Install:

```bash
pip install typer[all] rich pydantic-settings
python ops_cli.py --help
```

---

## 4. Global context and verbosity

Pass shared state via Typer context:

```python
import typer
from typing import Optional

app = typer.Typer(help="Handbook ops CLI")
state = {"verbose": False, "dry_run": False}

@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print actions only"),
    profile: Optional[str] = typer.Option(None, envvar="OPS_PROFILE"),
):
    state["verbose"] = verbose
    state["dry_run"] = dry_run
    state["profile"] = profile
    if verbose:
        typer.echo(f"Profile: {profile or 'default'}")
```

Destructive commands check `dry_run` before mutating infrastructure.

---

## 5. Subcommands with typed options

```python
@app.command("scale")
def scale_service(
    name: str = typer.Argument(..., help="Deployment name"),
    replicas: int = typer.Option(..., min=0, max=50),
    namespace: str = typer.Option("default", "-n"),
    json_output: bool = typer.Option(False, "--json"),
):
    action = {"action": "scale", "name": name, "replicas": replicas, "namespace": namespace}
    if state["dry_run"]:
        typer.echo(f"[dry-run] would scale: {action}")
        raise typer.Exit(0)
    if json_output:
        typer.echo(json.dumps(action))
    else:
        typer.echo(f"Scaled {name} to {replicas} in {namespace}")
```

Enums and path validation:

```python
from enum import Enum

class Environment(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"

@app.command()
def deploy(env: Environment, manifest: Path = typer.Argument(..., exists=True)):
    ...
```

---

## 6. Exit codes and errors

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure |
| 2 | Usage error (Click default) |
| 3+ | Domain-specific (document in `--help`) |

```python
try:
    result = run_deploy(env, manifest)
except DeployError as exc:
    typer.secho(f"Deploy failed: {exc}", fg=typer.colors.RED, err=True)
    raise typer.Exit(1)
```

Never `sys.exit()` with stack traces for expected failures — print actionable messages.

---

## 7. Click equivalent (when you need more control)

```python
import click

@click.group()
@click.option("--verbose", is_flag=True)
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

@cli.command()
@click.argument("name")
@click.option("--replicas", type=int, required=True)
@click.pass_context
def scale(ctx, name, replicas):
    if ctx.obj["verbose"]:
        click.echo(f"Scaling {name}")
    ...
```

Use Click when you need complex argument nesting or custom parameter types Typer doesn't expose cleanly.

---

## 8. Testing CLIs

```python
from typer.testing import CliRunner
from ops_cli import app

runner = CliRunner()

def test_scale_dry_run():
    result = runner.invoke(app, ["--dry-run", "scale", "web", "--replicas", "3"])
    assert result.exit_code == 0
    assert "dry-run" in result.stdout
```

Test `--help`, error paths, and JSON output — these are your CLI contract.

---

## 9. Packaging entry points

When published via Poetry (Day 28):

```toml
[tool.poetry.scripts]
ops = "handbook_ops.cli:app"
```

Users run `ops scale web --replicas 5` from anywhere in PATH.

---

## 10. Lab — Day 24

Work from `python/day24/labs/`.

1. Run `python ops_cli.py --help` and explore subcommands.
2. `python ops_cli.py hosts list --json` — inspect JSON host registry.
3. `python ops_cli.py --dry-run deploy staging deploy.valid.yaml` — confirm no changes applied.
4. `python ops_cli.py --verbose deploy dev deploy.valid.yaml`.
5. Trigger validation error: `python ops_cli.py deploy prod deploy.invalid.yaml` — exit code 1.
6. Run `python ops_cli.py hosts get web1`.
7. **Stretch:** Add shell completion: `ops_cli.py --install-completion` (Typer built-in).

**Success criteria:** All subcommands respond with correct exit codes; `--dry-run` never mutates state.

---

## 11. DevOps connections

- **kubectl-style UX:** Operators expect `-n`, `-o json`, and consistent verbs — mirror cloud-native conventions.
- **CI integration:** Jenkins/GitHub Actions call your CLI with `--json` and parse results.
- **Runbooks:** Replace bash one-liners with versioned CLI subcommands that encode guardrails.

---

## Quick reference

| Task | Command |
|------|---------|
| Help | `python ops_cli.py --help` |
| Dry run | `python ops_cli.py --dry-run deploy staging file.yaml` |
| JSON output | `python ops_cli.py hosts list --json` |
| Verbose | `python ops_cli.py -v hosts get web1` |
| Test CLI | `pytest tests/test_cli.py` |

**Next:** [Day 25 — FastAPI for internal ops tools](../day25/)
