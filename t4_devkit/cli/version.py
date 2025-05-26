from __future__ import annotations

import importlib
import importlib.metadata

import typer
from rich.console import Console

console = Console()


def version_callback(value: bool) -> None:
    if value:
        version = importlib.metadata.version("t4-devkit")
        console.print(f"[bold green]t4viz[/bold green]: [cyan]{version}[/cyan]")
        raise typer.Exit()
