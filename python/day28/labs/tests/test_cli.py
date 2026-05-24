"""Tests for handbook-tool package."""
from typer.testing import CliRunner

from handbook_tool.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "handbook-tool" in result.stdout


def test_echo():
    result = runner.invoke(app, ["echo", "hello"])
    assert result.exit_code == 0
    assert "hello" in result.stdout
