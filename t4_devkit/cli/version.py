from __future__ import annotations

import importlib
import importlib.metadata

import typer
from rich.console import Console


def version_callback(ctx: typer.Context, value: bool) -> None:
    if value:
        version = importlib.metadata.version("t4-devkit")
        console = Console()
        console.print(f"[bold green]{ctx.info_name}[/bold green]: [cyan]{version}[/cyan]")
        raise typer.Exit()
