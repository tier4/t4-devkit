from __future__ import annotations

import importlib.metadata
import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Sequence

import numpy as np
import pypcd4
from PIL import Image

from t4_devkit.common.io import file_sha256, save_pointcloud, save_video
from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses

from .manifest import MANIFEST_FILENAME, Capabilities, Manifest
from .name import SchemaName

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = ["DatasetWriter"]


class DatasetWriter:
    """Write a T4Dataset 1.0 dataset folder: sensor data, then tables and `manifest.json`.

    The writer writes files; the caller decides their content. Data files go first, then
    `save` writes the tables and the manifest, with the hash of every file in the folder.

    A channel is stored as one file (`write_lidar`: Parquet, `write_camera`: AV1 video), the
    default, or as one file per frame (`write_lidar_frame`: BIN or PCD, `write_image`: JPEG or
    PNG), the opt-in for workflows that read files directly. Point labels need Parquet. `copy`
    keeps a file or folder as it is.

    Examples:
        >>> writer = DatasetWriter("out/<DATASET_ID>/<DATASET_VERSION>")
        >>> path, frame_count = writer.write_lidar("LIDAR_TOP", frames, fields)
        >>> writer.copy("in/map/lanelet2_map.osm", "map/lanelet2_map.osm")
        >>> manifest = writer.save(tables, manifest_info)
    """

    def __init__(self, output_root: PathLike) -> None:
        """
        Args:
            output_root (PathLike): Dataset root to create, i.e. `<DATASET_ID>/<DATASET_VERSION>`.

        Raises:
            FileExistsError: If the folder already exists: a dataset is never written in place.
        """
        self.output_root = Path(output_root)
        if self.output_root.exists():
            raise FileExistsError(f"{self.output_root} already exists")
        self.output_root.mkdir(parents=True)

    def write_lidar(
        self,
        channel: str,
        frames: Iterable[Mapping[str, np.ndarray]],
        fields: Sequence[tuple[str, str]],
        **kwargs: Any,
    ) -> tuple[str, int]:
        """Write the frames of a LiDAR channel to `data/<CHANNEL>/<CHANNEL>.parquet`.

        Args:
            channel (str): Channel name.
            frames (Iterable[Mapping[str, np.ndarray]]): Point fields per frame.
            fields (Sequence[tuple[str, str]]): (name, dtype) of each column.
            **kwargs: Options of `save_pointcloud`.

        Returns:
            The path relative to the dataset root and the number of frames.

        Raises:
            FileExistsError: If the channel's file is already written.
        """
        path = self._data_path(channel, "parquet")
        frame_count = save_pointcloud(self.output_root / path, frames, fields, **kwargs)
        return path, frame_count

    def write_camera(
        self,
        channel: str,
        frames: Iterable[np.ndarray],
        frame_rate: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Write the frames of a camera channel to `data/<CHANNEL>/<CHANNEL>.mp4`.

        Args:
            channel (str): Channel name.
            frames (Iterable[np.ndarray]): RGB images.
            frame_rate (int): Frames per second.
            **kwargs: Options of `save_video`.

        Returns:
            The values of `sensor.camera.video`, `path` included.

        Raises:
            FileExistsError: If the channel's file is already written.
        """
        path = self._data_path(channel, "mp4")
        video = save_video(self.output_root / path, frames, frame_rate, **kwargs)
        return {"path": path} | video

    def write_lidar_frame(
        self,
        channel: str,
        frame_index: int,
        points: Mapping[str, np.ndarray],
        fields: Sequence[tuple[str, str]],
        fileformat: str = "bin",
    ) -> str:
        """Write one LiDAR frame as its own file, `data/<CHANNEL>/<FRAME_INDEX>.bin` or `.pcd`.

        The sensor row of such a channel has `lidar.container.format` "bin" or "pcd" and
        `path` null; its records have `frame_index` null and the file as `filename`.

        Args:
            channel (str): Channel name.
            frame_index (int): Position of the frame in the channel; the file is named after it.
            points (Mapping[str, np.ndarray]): Arrays of shape (N,) keyed by field name.
            fields (Sequence[tuple[str, str]]): (name, dtype) of each field, in file order, e.g.
                from `sensor.lidar.fields`.
            fileformat (str, optional): "bin" (raw records without header, read with `fields`)
                or "pcd" (binary PCD, self-described).

        Returns:
            The path relative to the dataset root.

        Raises:
            FileExistsError: If the frame's file is already written.
        """
        if fileformat not in ("bin", "pcd"):
            raise ValueError(f"fileformat must be 'bin' or 'pcd', got {fileformat!r}")
        path = self._frame_path(channel, frame_index, fileformat)
        columns = [np.asarray(points[name], dtype=dtype) for name, dtype in fields]
        if fileformat == "bin":
            frame = np.empty(len(columns[0]), dtype=np.dtype([tuple(field) for field in fields]))
            for (name, _), column in zip(fields, columns):
                frame[name] = column
            frame.tofile(self.output_root / path)
        else:
            names, dtypes = zip(*fields)
            pypcd4.PointCloud.from_points(columns, names, dtypes).save(self.output_root / path)
        return path

    def write_image(
        self,
        channel: str,
        frame_index: int,
        image: bytes | np.ndarray,
        fileformat: str = "jpg",
    ) -> str:
        """Write one camera frame as its own file, `data/<CHANNEL>/<FRAME_INDEX>.jpg` or `.png`.

        Encoded bytes (e.g. a JPEG read from a rosbag) are written as they are, without
        decoding; an RGB array is encoded with Pillow. The sensor row of such a channel has
        `camera.video` null; its records have `frame_index` null and the file as `filename`.

        Args:
            channel (str): Channel name.
            frame_index (int): Position of the frame in the channel; the file is named after it.
            image (bytes | np.ndarray): Encoded image in the given format, or an RGB image of
                shape (H, W, 3).
            fileformat (str, optional): "jpg" or "png".

        Returns:
            The path relative to the dataset root.

        Raises:
            FileExistsError: If the frame's file is already written.
        """
        if fileformat not in ("jpg", "png"):
            raise ValueError(f"fileformat must be 'jpg' or 'png', got {fileformat!r}")
        path = self._frame_path(channel, frame_index, fileformat)
        if isinstance(image, bytes):
            (self.output_root / path).write_bytes(image)
        else:
            Image.fromarray(image).save(self.output_root / path)
        return path

    def copy(self, source: PathLike, path: str) -> None:
        """Copy a file or folder as it is, e.g. the map, `input_bag/` or per-frame images.

        Args:
            source (PathLike): File or folder to copy.
            path (str): Destination relative to the dataset root.
        """
        destination = self.output_root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if Path(source).is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    def save(
        self,
        tables: Mapping[SchemaName, Sequence[Any]],
        manifest_info: Mapping[str, Any],
    ) -> Manifest:
        """Write the tables and `manifest.json`.

        Every required table is written, and every optional table with records. The manifest
        lists them and every file under `data/`, `map/` and `input_bag/` with its hash and size.
        Its `capabilities` are computed from the tables unless given, and t4-devkit is added to
        its `generators`.

        Args:
            tables (Mapping[SchemaName, Sequence[Any]]): 1.0 records per table.
            manifest_info (Mapping[str, Any]): The other `manifest.json` fields: identity,
                provenance, migration notes, ...

        Returns:
            The manifest written.
        """
        table_entries = {}
        for table in SchemaName:
            records = tables.get(table, [])
            if not records and table.is_optional():
                continue
            path = f"annotation/{table.filename}"
            self._write_json(path, serialize_dataclasses(list(records)))
            table_entries[table.value] = {"path": path, "sha256": self._sha256(path)}

        assets = [
            {
                "path": path,
                "sha256": self._sha256(path),
                "bytes": (self.output_root / path).stat().st_size,
            }
            for path in self._asset_paths()
        ]
        generator = {"name": "t4-devkit", "version": importlib.metadata.version("t4-devkit")}
        generators = list(manifest_info.get("generators", []))
        if generator not in generators:
            generators.append(generator)
        capabilities = manifest_info.get("capabilities") or Capabilities.from_tables(tables)

        data = dict(manifest_info)
        data.update(
            generators=generators,
            capabilities=capabilities,
            tables=table_entries,
            assets=assets,
        )
        manifest = Manifest(**data)
        self._write_json(MANIFEST_FILENAME, serialize_dataclass(manifest))
        return manifest

    def _data_path(self, channel: str, extension: str) -> str:
        path = f"data/{channel}/{channel}.{extension}"
        if (self.output_root / path).exists():
            raise FileExistsError(f"{path} is already written: a channel has one file")
        (self.output_root / path).parent.mkdir(parents=True, exist_ok=True)
        return path

    def _frame_path(self, channel: str, frame_index: int, extension: str) -> str:
        path = f"data/{channel}/{frame_index:05d}.{extension}"
        if (self.output_root / path).exists():
            raise FileExistsError(f"{path} is already written")
        (self.output_root / path).parent.mkdir(parents=True, exist_ok=True)
        return path

    def _asset_paths(self) -> list[str]:
        """Return every file under the asset folders, relative to the dataset root, sorted."""
        return sorted(
            filepath.relative_to(self.output_root).as_posix()
            for directory in Manifest.ASSET_DIRS
            for filepath in (self.output_root / directory).rglob("*")
            if filepath.is_file()
        )

    def _write_json(self, path: str, data: Any) -> None:
        filepath = self.output_root / path
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def _sha256(self, path: str) -> str:
        return file_sha256(self.output_root / path)
