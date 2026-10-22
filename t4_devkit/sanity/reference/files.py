"""Reading 1.0 channel files for the file reference rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import av
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ..result import Reason

if TYPE_CHECKING:
    from pathlib import Path

    from t4_devkit.schema.v1 import Sensor

__all__ = ["describe_lidar_file", "describe_video_file", "lidar_column_values"]


def describe_lidar_file(sensor: Sensor, path: Path) -> list[Reason]:
    """Return the differences between a LiDAR Parquet file and its sensor row (columns, dtypes,
    frames)."""
    parquet = pq.ParquetFile(path)
    columns = [(field.name, _numpy_dtype(field.type)) for field in parquet.schema_arrow]
    declared = [(field.name, field.dtype) for field in sensor.lidar.fields]
    failures = []
    if columns != declared:
        failures.append(Reason(f"Sensor {sensor.channel}: columns {columns}, declared {declared}"))
    if parquet.num_row_groups != sensor.lidar.container.frame_count:
        failures.append(
            Reason(
                f"Sensor {sensor.channel}: {parquet.num_row_groups} row groups, "
                f"'frame_count' {sensor.lidar.container.frame_count}"
            )
        )
    return failures


def describe_video_file(sensor: Sensor, path: Path) -> list[Reason]:
    """Return the differences between a camera video and its sensor row (codec, pixels, timing,
    size)."""
    camera, video = sensor.camera, sensor.camera.video
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        frame = next(container.decode(stream))
        actual = {
            "codec": stream.codec_context.codec.name,
            "pixel_format": frame.format.name,
            "bit_depth": frame.format.components[0].bits,
            "timescale": stream.time_base.denominator,
            "frame_count": stream.frames,
            "size": (frame.width, frame.height),
        }
    expected = {
        "codec": "av1",
        "pixel_format": video.pixel_format.split()[0],
        "bit_depth": video.bit_depth,
        "timescale": video.timescale,
        "frame_count": video.frame_count,
        "size": (camera.width, camera.height),
    }
    # decoders of AV1 have their own names (libdav1d, libaom-av1, ...)
    if "av1" in actual["codec"]:
        actual["codec"] = "av1"
    return [
        Reason(f"Sensor {sensor.channel}: {name} {actual[name]}, declared {expected[name]}")
        for name in expected
        if actual[name] != expected[name]
    ]


def lidar_column_values(path: Path, column: str) -> set | None:
    """Return the distinct non-null values of a column of a LiDAR Parquet file, or None if it has
    no such column."""
    parquet = pq.ParquetFile(path)
    if column not in parquet.schema_arrow.names:
        return None
    values = pc.unique(parquet.read(columns=[column]).column(column)).drop_null()
    return set(values.to_pylist())


def lidar_partly_null_frames(path: Path, column: str) -> list[int] | None:
    """Return the frames of a LiDAR Parquet file where a column is null on some points but not
    all, or None if it has no such column."""
    parquet = pq.ParquetFile(path)
    if column not in parquet.schema_arrow.names:
        return None
    frames = []
    for i in range(parquet.num_row_groups):
        nulls = parquet.read_row_group(i, columns=[column]).column(column).null_count
        if 0 < nulls < parquet.metadata.row_group(i).num_rows:
            frames.append(i)
    return frames


def _numpy_dtype(arrow_type: pa.DataType) -> str:
    """Return the NumPy name of an Arrow type, as `sensor.lidar.fields` writes it (e.g. "float32")."""
    return pa.array([], type=arrow_type).to_numpy(zero_copy_only=False).dtype.name
