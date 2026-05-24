#!/usr/bin/env python3
"""Handbook ops CLI — Typer-based operator tool."""
from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

# Allow importing Day 23 models from sibling path when run standalone
LABS_ROOT = Path(__file__).resolve().parent
DAY23 = LABS_ROOT.parent.parent / "day23" / "labs"
if DAY23.exists() and str(DAY23) not in sys.path:
    sys.path.insert(0, str(DAY23))

from models import DeployConfig  # noqa: E402

app = typer.Typer(help="Handbook ops CLI for deploy and host management")
console = Console()

state: dict = {"verbose": False, "dry_run": False, "profile": None}

HOSTS_FILE = LABS_ROOT / "hosts.json"


class Environment(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"


def load_hosts() -> list[dict]:
    return json.loads(HOSTS_FILE.read_text())


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print actions without applying"),
    profile: Optional[str] = typer.Option(None, "--profile", envvar="OPS_PROFILE"),
) -> None:
    state["verbose"] = verbose
    state["dry_run"] = dry_run
    state["profile"] = profile
    if verbose and profile:
        console.print(f"[dim]Using profile: {profile}[/dim]")


hosts_app = typer.Typer(help="Host registry commands")
app.add_typer(hosts_app, name="hosts")


@hosts_app.command("list")
def hosts_list(json_output: bool = typer.Option(False, "--json")) -> None:
    """List registered hosts."""
    hosts = load_hosts()
    if json_output:
        console.print_json(json.dumps(hosts))
        return
    table = Table(title="Hosts")
    table.add_column("Name")
    table.add_column("Group")
    table.add_column("Env")
    for host in hosts:
        table.add_row(host["name"], host.get("group", ""), host.get("env", ""))
    console.print(table)


@hosts_app.command("get")
def hosts_get(name: str) -> None:
    """Show details for one host."""
    for host in load_hosts():
        if host["name"] == name:
            console.print_json(json.dumps(host))
            return
    console.print(f"[red]Host not found: {name}[/red]", stderr=True)
    raise typer.Exit(1)


@app.command("deploy")
def deploy(
    env: Environment,
    manifest: Path = typer.Argument(..., exists=True, readable=True),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Validate and apply a deployment manifest."""
    try:
        config = DeployConfig.model_validate(yaml.safe_load(manifest.read_text()))
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"])
            console.print(f"[red]ERROR {loc}: {err['msg']}[/red]")
        raise typer.Exit(1)

    spec = config.deployment
    action = {
        "env": env.value,
        "name": spec.name,
        "replicas": spec.replicas,
        "image": spec.image,
        "dry_run": state["dry_run"],
    }

    if state["dry_run"]:
        console.print(f"[yellow][dry-run][/yellow] would deploy: {action}")
        raise typer.Exit(0)

    if state["verbose"]:
        console.print(f"Deploying {spec.name} to {env.value}...")

    if json_output:
        console.print_json(json.dumps({"status": "applied", **action}))
    else:
        console.print(f"[green]Applied[/green] {spec.name} ({spec.replicas} replicas) → {env.value}")


@app.command("scale")
def scale(
    name: str = typer.Argument(..., help="Service name"),
    replicas: int = typer.Option(..., "--replicas", min=0, max=50),
    namespace: str = typer.Option("default", "-n", "--namespace"),
) -> None:
    """Scale a service (simulated)."""
    action = {"name": name, "replicas": replicas, "namespace": namespace}
    if state["dry_run"]:
        console.print(f"[yellow][dry-run][/yellow] would scale: {action}")
        raise typer.Exit(0)
    console.print(f"Scaled {name} to {replicas} in namespace {namespace}")


if __name__ == "__main__":
    app()
