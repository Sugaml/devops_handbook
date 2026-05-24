"""Tests for Typer CLI."""
from __future__ import annotations

from typer.testing import CliRunner

from incident_toolkit.cli import app

runner = CliRunner()


def test_inventory_command():
    result = runner.invoke(app, ["inventory"])
    assert result.exit_code == 0
    assert "webservers" in result.stdout or "web1" in result.stdout


def test_inventory_json():
    result = runner.invoke(app, ["inventory", "--json"])
    assert result.exit_code == 0
    assert "web1" in result.stdout


def test_assess_json(tmp_path):
    targets = tmp_path / "targets.yaml"
    targets.write_text(
        "targets:\n  - name: bad\n    url: http://127.0.0.1:1\n    expected_status: 200\n"
    )
    result = runner.invoke(app, ["assess", str(targets), "--json"])
    assert result.exit_code == 1
    assert "unhealthy" in result.stdout
