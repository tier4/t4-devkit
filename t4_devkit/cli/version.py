from __future__ import annotations

import importlib
import importlib.metadata

import click
import typer
from rich.console import Console

console = Console()


def version_callback(value: bool) -> None:
    if value:
        ctx = click.get_current_context()
        version = importlib.metadata.version("t4-devkit")
        console.print(f"[bold green]{ctx.info_name}[/bold green]: [cyan]{version}[/cyan]")
        raise typer.Exit()
