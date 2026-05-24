"""Ansible playbook execution with safety guardrails."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import structlog

from incident_toolkit.config import settings
from incident_toolkit.inventory import load_hosts, to_ansible_inventory
from incident_toolkit.models import PlaybookResult, RemediateResult

log = structlog.get_logger()


def validate_playbook_path(playbook: Path) -> Path:
    resolved = playbook.resolve()
    approved = settings.approved_playbook_dir.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Playbook not found: {playbook}")
    if approved.exists() and approved not in resolved.parents and resolved.parent != approved:
        raise PermissionError(f"Playbook must live under {approved}")
    return resolved


def write_temp_inventory() -> Path:
    hosts = load_hosts()
    inv = to_ansible_inventory(hosts)
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(inv, tmp)
    tmp.close()
    return Path(tmp.name)


def run_playbook(
    playbook: Path,
    *,
    dry_run: bool = True,
    limit: str | None = None,
) -> PlaybookResult:
    playbook = validate_playbook_path(playbook)
    inventory_file = write_temp_inventory()
    cmd = ["ansible-playbook", str(playbook), "-i", str(inventory_file)]
    if dry_run:
        cmd.append("--check")
    if limit:
        cmd.extend(["--limit", limit])

    log.info("ansible_playbook_start", playbook=str(playbook), dry_run=dry_run, cmd=cmd)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log.info(
        "ansible_playbook_finished",
        rc=proc.returncode,
        dry_run=dry_run,
        stdout_lines=len(proc.stdout.splitlines()),
    )
    return PlaybookResult(
        playbook=str(playbook),
        rc=proc.returncode,
        dry_run=dry_run,
        stdout=proc.stdout,
    )


def remediate(
    incident_id: str,
    playbook: Path,
    *,
    dry_run: bool = True,
    limit: str | None = None,
) -> RemediateResult:
    result = run_playbook(playbook, dry_run=dry_run, limit=limit)
    return RemediateResult(
        incident_id=incident_id,
        playbook=str(playbook),
        dry_run=dry_run,
        success=result.rc == 0,
        rc=result.rc,
    )
