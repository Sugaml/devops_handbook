"""CLI entrypoint for handbook-tool."""
from __future__ import annotations

import typer
from rich.console import Console

from handbook_tool import __version__

app = typer.Typer(help="Handbook internal ops CLI")
console = Console()


@app.command()
def version() -> None:
    """Print package version."""
    console.print(f"handbook-tool {__version__}")


@app.command()
def echo(message: str) -> None:
    """Echo a message (connectivity smoke test)."""
    console.print(message)


if __name__ == "__main__":
    app()
