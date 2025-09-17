"""CLI command for T4 to ROS bag conversion."""

from __future__ import annotations

import os
from typing import Annotated

import typer

from t4_devkit.rosbag.pipeline import T4ToRosbagPipeline

from .version import version_callback

cli = typer.Typer(
    name="t4rosbag",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


def _create_dir(output: str | None) -> None:
    """Create output directory if specified."""
    if output is not None:
        os.makedirs(output, exist_ok=True)


@cli.command("convert", help="Convert T4 dataset to ROS bag format.")
def convert(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the T4 dataset.")],
    output: Annotated[str, typer.Option(
        ...,
        "-o",
        "--output",
        help="Output directory for ROS bag files.",
    )],
    source_bag: Annotated[
        str | None,
        typer.Option(
            ...,
            "-b",
            "--source-bag",
            help="Path to source ROS bag to copy all topics from (optional).",
        ),
    ] = None,
    revision: Annotated[
        str | None,
        typer.Option(
            ..., "-rv", "--revision", help="Specify if you want to load the specific version."
        ),
    ] = None,
    scene: Annotated[
        str | None,
        typer.Option(
            ..., "-s", "--scene", help="Specific scene token to convert (converts all scenes if not specified)."
        ),
    ] = None,
    interpolation_hz: Annotated[
        float,
        typer.Option(
            ...,
            "-hz",
            "--interpolation-hz",
            help="Interpolation frequency in Hz for output messages.",
        ),
    ] = 10.0,
    topic_name: Annotated[
        str,
        typer.Option(
            ...,
            "-t",
            "--topic",
            help="ROS topic name for tracked objects.",
        ),
    ] = "/annotation/object_recognition/tracked_objects",
    frame_id: Annotated[
        str,
        typer.Option(
            ...,
            "-f",
            "--frame-id",
            help="Frame ID for ROS messages.",
        ),
    ] = "map",
) -> None:
    """Convert T4 dataset to ROS bag format with tracked objects."""
    _create_dir(output)

    # Create conversion pipeline
    pipeline = T4ToRosbagPipeline(
        t4_data_root=data_root,
        output_path=output,
        source_bag_path=source_bag,
        revision=revision,
        interpolation_hz=interpolation_hz,
        topic_name=topic_name,
        frame_id=frame_id
    )

    # Print conversion statistics
    stats = pipeline.get_conversion_stats()
    print(f"Dataset statistics:")
    print(f"  - Total scenes: {stats['total_scenes']}")
    print(f"  - Total samples: {stats['total_samples']}")
    print(f"  - Total 3D annotations: {stats['total_3d_annotations']}")
    print(f"  - Interpolation frequency: {stats['interpolation_hz']} Hz")
    print(f"  - Output path: {stats['output_path']}")
    print()

    try:
        if scene is not None:
            # Convert specific scene
            print(f"Converting specific scene: {scene}")
            pipeline.convert_scene(scene)
        else:
            # Convert all scenes
            print("Converting all scenes...")
            pipeline.convert_all_scenes()

        print("Conversion completed successfully!")
        print(f"ROS bag files saved to: {output}")

    except Exception as e:
        print(f"Error during conversion: {e}")
        raise typer.Exit(1)


@cli.command("list-scenes", help="List all scenes in the dataset.")
def list_scenes(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the T4 dataset.")],
    revision: Annotated[
        str | None,
        typer.Option(
            ..., "-rv", "--revision", help="Specify if you want to load the specific version."
        ),
    ] = None,
) -> None:
    """List all scenes in the T4 dataset."""
    try:
        pipeline = T4ToRosbagPipeline(
            t4_data_root=data_root,
            output_path="",  # Not used for listing
            revision=revision
        )

        print("Available scenes:")
        for scene in pipeline.t4.scene:
            sample_count = len(pipeline._get_scene_samples(scene.token))
            print(f"  - {scene.name} (token: {scene.token}, samples: {sample_count})")

    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise typer.Exit(1)


@cli.callback()
def callback(
    version: Annotated[bool, typer.Option("--version", help="Show version")] = False,
) -> None:
    """T4 to ROS bag conversion tool."""
    if version:
        version_callback(version)