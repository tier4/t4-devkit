from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Sequence

import numpy as np
import pyarrow.parquet as pq
import pypcd4
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = ("load_json", "save_json", "load_pointcloud")


def load_json(filename: PathLike) -> Any:
    """Load json data from specified filepath.

    Args:
        filename (PathLike): File path to .json file.

    Returns:
        Loaded data.
    """
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def save_json(data: Any, filename: PathLike) -> None:
    """Save data into json file.

    Args:
        data (Any): Data to be saved.
        filename (PathLike): File path to save as json.
    """
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_pointcloud(
    filepath: PathLike,
    *,
    frame_index: int | None = None,
    fields: Sequence[tuple[str, str]] | None = None,
    columns: Sequence[str] | None = None,
) -> dict[str, np.ndarray]:
    """Load one pointcloud frame as one array per point field, in the dtype stored in the file.

    The layout is read from the file itself (`.parquet`, `.pcd`), or from `fields` for `.bin`,
    which has no header. Compression and encodings are read from the file.

    Args:
        filepath (PathLike): `.parquet` file of a channel, or `.pcd` / `.bin` file of one frame.
        frame_index (int | None, optional): Frame to read from a `.parquet` file (one row group per frame).
        fields (Sequence[tuple[str, str]] | None, optional): (name, dtype) of each point field
            of a `.bin` file, in order, e.g. from `sensor.lidar.fields`.
        columns (Sequence[str] | None, optional): Fields to return; all fields if None.

    Returns:
        Arrays of shape (N,) keyed by field name, in file order. A `.parquet` column that is
        null on every point of the frame is left out.
    """
    filepath = os.fspath(filepath)
    if filepath.endswith(".parquet"):
        if frame_index is None:
            raise ValueError("frame_index is required for a .parquet file")
        mtime = os.stat(filepath).st_mtime_ns
        frame = _open_parquet(filepath, mtime, os.getpid()).read_row_group(
            frame_index, columns=columns
        )
        # a column null on every point (e.g. point labels of a frame without labels) is left out
        return {
            name: frame[name].to_numpy()
            for name in frame.column_names
            if frame.num_rows == 0 or frame[name].null_count < frame.num_rows
        }

    if filepath.endswith(".pcd"):
        data = pypcd4.PointCloud.from_path(filepath).pc_data
    elif filepath.endswith(".bin"):
        if fields is None:
            raise ValueError("fields is required for a .bin file")
        data = np.fromfile(filepath, dtype=np.dtype(list(fields)))
    else:
        raise ValueError(f"Unexpected filetype: {filepath}")

    names = data.dtype.names if columns is None else columns
    return {name: data[name] for name in names}


@lru_cache(maxsize=32)
def _open_parquet(filepath: str, mtime: int, pid: int) -> pq.ParquetFile:
    """Open a Parquet file once per process and file version, memory-mapped.

    Reopening per frame re-reads the footer. `mtime` and `pid` are only part of the cache key,
    so a rewritten file or a forked worker gets its own handle.
    """
    return pq.ParquetFile(filepath, memory_map=True)
