"""Typer CLI for incident response workflows."""
from __future__ import annotations

import asyncio
import json
from enum import Enum
from pathlib import Path
from typing import Optional

import structlog
import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from incident_toolkit.config import settings
from incident_toolkit.health import assess
from incident_toolkit.inventory import build_inventory_groups, load_hosts
from incident_toolkit.logging_setup import configure_logging
from incident_toolkit.metrics import ASSESS_TOTAL, REMEDIATE_TOTAL
from incident_toolkit.models import IncidentContext

app = typer.Typer(help="Incident response toolkit")
console = Console()
state: dict = {"verbose": False}


class Environment(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"


class Severity(str, Enum):
    sev1 = "sev1"
    sev2 = "sev2"
    sev3 = "sev3"


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    log_json: bool = typer.Option(settings.log_json, "--log-json/--log-console"),
) -> None:
    state["verbose"] = verbose
    configure_logging(json_output=log_json)


def _ctx(
    env: Environment,
    severity: Severity,
    incident_id: Optional[str],
    dry_run: bool,
) -> IncidentContext:
    kwargs: dict = {
        "environment": env.value,
        "severity": severity.value,
        "dry_run": dry_run,
    }
    if incident_id:
        kwargs["incident_id"] = incident_id
    return IncidentContext(**kwargs)


@app.command()
def assess(
    targets: Path = typer.Argument(..., exists=True, readable=True),
    env: Environment = typer.Option(Environment.staging, "--env"),
    severity: Severity = typer.Option(Severity.sev2, "--severity"),
    incident_id: Optional[str] = typer.Option(None, "--incident-id"),
    concurrency: int = typer.Option(settings.default_concurrency, "--concurrency"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run concurrent health checks and summarize fleet status."""
    ctx = _ctx(env, severity, incident_id, dry_run=True)
    structlog.contextvars.bind_contextvars(incident_id=ctx.incident_id, command="assess")
    log = structlog.get_logger()

    result = asyncio.run(assess(targets, ctx, concurrency=concurrency))
    status = "healthy" if result.summary.unhealthy == 0 else "unhealthy"
    ASSESS_TOTAL.labels(status=status).inc()
    log.info(
        "assess_complete",
        total=result.summary.total,
        unhealthy=result.summary.unhealthy,
    )

    if json_output:
        console.print_json(result.model_dump_json())
        if result.unhealthy:
            raise typer.Exit(1)
        return

    console.print(f"Incident [bold]{ctx.incident_id}[/bold] — {env.value}")
    console.print(
        f"Checked {result.summary.total}: "
        f"[green]{result.summary.healthy} healthy[/green], "
        f"[red]{result.summary.unhealthy} unhealthy[/red]"
    )
    for check in result.results:
        mark = "OK" if check.ok else "FAIL"
        detail = check.error or f"HTTP {check.status_code}"
        console.print(f"  [{mark}] {check.name} ({check.latency_ms}ms) — {detail}")

    if result.unhealthy:
        raise typer.Exit(1)


@app.command()
def inventory(json_output: bool = typer.Option(False, "--json")) -> None:
    """Display host registry grouped by Ansible group."""
    groups = build_inventory_groups(load_hosts())
    if json_output:
        payload = [g.model_dump() for g in groups]
        console.print_json(json.dumps(payload))
        return

    table = Table(title="Host inventory")
    table.add_column("Group")
    table.add_column("Host")
    table.add_column("IP")
    table.add_column("Env")
    for group in groups:
        for host in group.hosts:
            table.add_row(group.name, host.name, host.ansible_host, host.env)
    console.print(table)


@app.command()
def remediate(
    playbook: Path = typer.Option(..., "--playbook", exists=True),
    env: Environment = typer.Option(Environment.staging, "--env"),
    incident_id: Optional[str] = typer.Option(None, "--incident-id"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    limit: Optional[str] = typer.Option(None, "--limit"),
) -> None:
    """Run an approved Ansible playbook (dry-run by default)."""
    from incident_toolkit.ansible_ops import remediate as run_remediate

    if env == Environment.prod and not limit:
        console.print("[red]Production remediation requires --limit[/red]")
        raise typer.Exit(2)

    ctx = _ctx(env, Severity.sev2, incident_id, dry_run=dry_run)
    structlog.contextvars.bind_contextvars(incident_id=ctx.incident_id, command="remediate")
    log = structlog.get_logger()

    try:
        result = run_remediate(ctx.incident_id, playbook, dry_run=dry_run, limit=limit)
    except (FileNotFoundError, PermissionError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc

    status = "success" if result.success else "failed"
    REMEDIATE_TOTAL.labels(status=status, dry_run=str(dry_run).lower()).inc()
    log.info("remediate_complete", success=result.success, rc=result.rc, dry_run=dry_run)

    mode = "dry-run" if dry_run else "LIVE"
    color = "green" if result.success else "red"
    console.print(f"[{color}]{mode} remediation rc={result.rc}[/{color}] playbook={playbook}")
    if not result.success:
        raise typer.Exit(1)


@app.command("serve-api")
def serve_api(
    port: int = typer.Option(settings.metrics_port, "--port"),
    host: str = typer.Option("127.0.0.1", "--host"),
) -> None:
    """Start FastAPI server with health and metrics endpoints."""
    from incident_toolkit.api import create_app

    structlog.get_logger().info("api_start", host=host, port=port)
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    app()
