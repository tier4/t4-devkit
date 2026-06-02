from __future__ import annotations

import json
import os
from typing import Annotated

import typer

from t4_devkit import T4Devkit

from .version import version_callback

cli = typer.Typer(
    name="t4viz",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


@cli.command("scene", help="Visualize a specific scene.")
def scene(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    revision: Annotated[
        str | None,
        typer.Option(
            ..., "-rv", "--revision", help="Specify if you want to load the specific version."
        ),
    ] = None,
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
    use_rosbag: Annotated[
        bool,
        typer.Option(
            "--use-rosbag/--no-use-rosbag",
            help="Read LiDAR data from rosbag instead of .pcd.bin files.",
        ),
    ] = False,
    topic_mapping: Annotated[
        str | None,
        typer.Option(
            "--topic-mapping",
            help="Channel-to-topic mapping as JSON string or file path.",
        ),
    ] = None,
) -> None:
    _create_dir(output)

    mapping = _parse_topic_mapping(topic_mapping)
    t4 = T4Devkit(
        data_root,
        revision=revision,
        verbose=False,
        use_rosbag=use_rosbag,
        topic_mapping=mapping,
    )
    t4.render_scene(future_seconds=future, save_dir=output)


@cli.command("instance", help="Visualize a particular instance in the corresponding scene.")
def instance(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    instance: Annotated[list[str], typer.Argument(help="Instance token(s).")],
    revision: Annotated[
        str | None,
        typer.Option(
            ..., "-rv", "--revision", help="Specify if you want to load the specific version."
        ),
    ] = None,
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
    use_rosbag: Annotated[
        bool,
        typer.Option(
            "--use-rosbag/--no-use-rosbag",
            help="Read LiDAR data from rosbag instead of .pcd.bin files.",
        ),
    ] = False,
    topic_mapping: Annotated[
        str | None,
        typer.Option(
            "--topic-mapping",
            help="Channel-to-topic mapping as JSON string or file path.",
        ),
    ] = None,
) -> None:
    _create_dir(output)

    mapping = _parse_topic_mapping(topic_mapping)
    t4 = T4Devkit(
        data_root,
        revision=revision,
        verbose=False,
        use_rosbag=use_rosbag,
        topic_mapping=mapping,
    )
    t4.render_instance(instance_token=instance, future_seconds=future, save_dir=output)


@cli.command("pointcloud", help="Visualize pointcloud in the corresponding scene.")
def pointcloud(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    revision: Annotated[
        str | None,
        typer.Option(
            ..., "-rv", "--revision", help="Specify if you want to load the specific version."
        ),
    ] = None,
    output: Annotated[
        str | None,
        typer.Option(
            ...,
            "-o",
            "--output",
            help="Output directory to save recorded .rrd file.",
        ),
    ] = None,
    use_rosbag: Annotated[
        bool,
        typer.Option(
            "--use-rosbag/--no-use-rosbag",
            help="Read LiDAR data from rosbag instead of .pcd.bin files.",
        ),
    ] = False,
    topic_mapping: Annotated[
        str | None,
        typer.Option(
            "--topic-mapping",
            help="Channel-to-topic mapping as JSON string or file path.",
        ),
    ] = None,
) -> None:
    _create_dir(output)

    mapping = _parse_topic_mapping(topic_mapping)
    t4 = T4Devkit(
        data_root,
        revision=revision,
        verbose=False,
        use_rosbag=use_rosbag,
        topic_mapping=mapping,
    )
    t4.render_pointcloud(save_dir=output)


def _parse_topic_mapping(topic_mapping: str | None) -> list | None:
    """Parse topic mapping from a JSON string or file path.

    Args:
        topic_mapping (str | None): JSON string or path to a JSON file.

    Returns:
        List of TopicMapping instances, or None.
    """
    if topic_mapping is None:
        return None

    try:
        if os.path.isfile(topic_mapping):
            from t4_devkit.common.io import load_json

            raw = load_json(topic_mapping)
        else:
            raw = json.loads(topic_mapping)
    except Exception as e:
        raise typer.BadParameter(
            "--topic-mapping must be a JSON object (or a path to a JSON file) mapping channel -> topic"
        ) from e

    if not isinstance(raw, dict):
        raise typer.BadParameter("--topic-mapping must be a JSON object mapping channel -> topic")

    from t4_devkit.rosbag import TopicMapping

    try:
        return TopicMapping.from_dict(raw)
    except (TypeError, ValueError) as e:
        raise typer.BadParameter(str(e)) from e


def _create_dir(dir_path: str | None) -> None:
    """Create a directory with the specified path.

    If the input path is `None` this function does nothing.

    Args:
        dir_path (str | None): Directory path to create.
    """
    if dir_path is not None:
        os.makedirs(dir_path, exist_ok=True)


@cli.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the application version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    pass
