from __future__ import annotations

import importlib
import importlib.metadata
import os
from typing import Annotated

import typer
from rich.console import Console

from t4_devkit import Tier4

console = Console()

cli = typer.Typer(
    name="t4viz",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


@cli.command("scene", help="Visualize a specific scene.")
def scene(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    future: Annotated[
        float,
        typer.Option(
            ...,
            "-f",
            "--future",
            help="Future time seconds.",
        ),
    ] = 0.0,
    output: Annotated[
        str | None,
        typer.Option(
            ...,
            "-o",
            "--output",
            help="Output directory to save recorded .rrd file.",
        ),
    ] = None,
    show: Annotated[bool, typer.Option(help="Indicates whether to show viewer.")] = True,
) -> None:
    _create_dir(output)

    t4 = Tier4("annotation", data_root, verbose=False)
    scene_token = t4.scene[0].token
    t4.render_scene(scene_token, future_seconds=future, save_dir=output, show=show)


@cli.command("instance", help="Visualize a particular instance in the corresponding scene.")
def instance(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    instance: Annotated[str, typer.Argument(help="Instance token.")],
    future: Annotated[
        float,
        typer.Option(
            ...,
            "-f",
            "--future",
            help="Future time seconds.",
        ),
    ] = 0.0,
    output: Annotated[
        str | None,
        typer.Option(
            ...,
            "-o",
            "--output",
            help="Output directory to save recorded .rrd file.",
        ),
    ] = None,
    show: Annotated[bool, typer.Option(help="Indicates whether to show viewer.")] = True,
) -> None:
    _create_dir(output)

    t4 = Tier4("annotation", data_root, verbose=False)
    t4.render_instance(instance_token=instance, future_seconds=future, save_dir=output, show=show)


@cli.command("pointcloud", help="Visualize pointcloud in the corresponding scene.")
def pointcloud(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    ignore_distortion: Annotated[
        bool,
        typer.Option(
            ...,
            "-ig",
            "--ignore-distortion",
            help="Indicates whether to ignore camera distortion",
        ),
    ] = True,
    output: Annotated[
        str | None,
        typer.Option(
            ...,
            "-o",
            "--output",
            help="Output directory to save recorded .rrd file.",
        ),
    ] = None,
    show: Annotated[bool, typer.Option(help="Indicates whether to show viewer.")] = True,
) -> None:
    _create_dir(output)

    t4 = Tier4("annotation", data_root, verbose=False)
    scene_token = t4.scene[0].token
    t4.render_pointcloud(
        scene_token,
        ignore_distortion=ignore_distortion,
        save_dir=output,
        show=show,
    )


def _create_dir(dir_path: str | None) -> None:
    """Create a directory with the specified path.

    If the input path is `None` this function does nothing.

    Args:
        dir_path (str | None): Directory path to create.
    """
    if dir_path is not None:
        os.makedirs(dir_path, exist_ok=True)


def _version_callback(value: bool):
    if value:
        version = importlib.metadata.version("t4-devkit")
        console.print(f"[bold green]t4viz[/bold green]: [cyan]{version}[/cyan]")
        raise typer.Exit()


@cli.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the application version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


if __name__ == "__main__":
    cli()
