from __future__ import annotations

import os.path as osp
import warnings
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import numpy as np

from t4_devkit.common.io import V0_BIN_FIELDS, load_image, load_json, load_pointcloud

from .loader import load_dataset
from .name import SchemaName
from .sensor import LidarContainer, LidarField
from .writer import DatasetWriter

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

    from .manifest import Manifest
    from .sample_data import SampleData
    from .sensor import Sensor

__all__ = ["V0Migrator"]


class V0Migrator:
    """Migrate a 0.x dataset to a new 1.0 dataset folder; the 0.x dataset is only read.

    Tables are loaded as 1.0 records (`load_dataset`), then each channel's files are rewritten
    in the 1.0 layout and its `sensor` / `sample_data` records updated to point to them. What
    the migration had to decide is collected in `notes`, for `manifest.migration_notes`.

    Examples:
        >>> migrator = V0Migrator("<0.x dataset>", "out/<DATASET_ID>/<VERSION>")
        >>> manifest = migrator.migrate("<DATASET_ID>", <VERSION>)

        Or channel by channel:

        >>> for sensor in migrator.lidars():
        ...     migrator.migrate_lidar(sensor)
        >>> for sensor in migrator.cameras():
        ...     migrator.migrate_camera(sensor)  # or copy_images(sensor) to keep the files
    """

    def __init__(self, data_root: PathLike, output_root: PathLike) -> None:
        """
        Args:
            data_root (PathLike): 0.x dataset root, i.e. `<DATASET_ID>/<DATASET_VERSION>`.
            output_root (PathLike): 1.0 dataset root to create.
        """
        self.data_root = data_root
        self.dataset = load_dataset(data_root)
        self.writer = DatasetWriter(output_root)
        self.notes: list[str] = []
        self._v0_frames = {record["token"]: record for record in self._load_v0("sample_data")}
        self._v0_channels = {
            record["token"]: record["channel"] for record in self._load_v0("sensor")
        }
        self._sensor_indices = {
            sensor.channel: sensor.index for sensor in self.tables(SchemaName.SENSOR)
        }
        self._labels = {
            record["sample_data_token"]: record["filename"] for record in self._load_v0("lidarseg")
        }

    def lidars(self) -> list[Sensor]:
        """Return the LiDAR sensors with frames of their own."""
        with_frames = {frame.sensor_token for frame in self.tables(SchemaName.SAMPLE_DATA)}
        return [
            sensor
            for sensor in self.tables(SchemaName.SENSOR)
            if sensor.lidar is not None and sensor.token in with_frames
        ]

    def migrate_lidar(self, sensor: Sensor) -> None:
        """Write the frames of a LiDAR channel to one Parquet file and point its records to it.

        Point fields get their 1.0 dtypes; `source_index` / `source_timestamp` come from the
        0.x `.info` files, and `label` / `instance` from 0.x lidarseg (`instance` is 0: 0.x
        labels are semantic only; frames without labels are null).

        Args:
            sensor (Sensor): LiDAR sensor with frames.

        Raises:
            ValueError: If the points of a frame are not covered by its `.info` sources, or
                lidarseg is present but category 0 is not `unpainted`.
        """
        records = self._channel_frames(sensor)
        self._relink(sensor, records)
        source_fields = self._source_fields(records[0])
        fields = self._point_fields(sensor.channel, records, source_fields)
        if self._v0_frames[records[0].token].get("info_filename"):
            fields += [("source_index", "uint8"), ("source_timestamp", "int64")]
        if any(record.token in self._labels for record in records):
            self._check_unpainted()
            self._index_instances()
            fields += [("label", "uint8"), ("instance", "uint32")]

        frames = (self._lidar_frame(record, source_fields, fields) for record in records)
        path, frame_count = self.writer.write_lidar(sensor.channel, frames, fields)

        sensor.lidar.container = LidarContainer(
            format="parquet", path=path, frame_count=frame_count, compression="zstd"
        )
        sensor.lidar.fields = [LidarField(name=name, dtype=dtype) for name, dtype in fields]
        for frame_index, record in enumerate(records):
            record.filename = path
            record.frame_index = frame_index
            record.fileformat = "parquet"

        # Source LiDARs of a merged channel have no frames of their own: their points are in
        # this file, so they get its format and fields.
        with_frames = {lidar.token for lidar in self.lidars()}
        for source in self.tables(SchemaName.SENSOR):
            if source.channel in sensor.lidar.source_channels and source.token not in with_frames:
                source.lidar.container = LidarContainer(
                    format="parquet",
                    path=None,
                    frame_count=source.lidar.container.frame_count,
                    compression="zstd",
                )
                source.lidar.fields = list(sensor.lidar.fields)

    def cameras(self) -> list[Sensor]:
        """Return the camera sensors with frames."""
        with_frames = {frame.sensor_token for frame in self.tables(SchemaName.SAMPLE_DATA)}
        return [
            sensor
            for sensor in self.tables(SchemaName.SENSOR)
            if sensor.camera is not None and sensor.token in with_frames
        ]

    def migrate_camera(self, sensor: Sensor) -> None:
        """Encode the image frames of a camera channel as one AV1 video and point its records to it.

        Frames go in timestamp order, so `frame_index` is the position. Frames marked
        `is_valid: false` (blank images) are encoded like the others. The frame rate is the
        median interval between frames.

        Args:
            sensor (Sensor): Camera sensor with frames.

        Raises:
            ValueError: If an image does not have the sensor's width and height.
        """
        records = self._channel_frames(sensor)
        self._relink(sensor, records)
        images = (self._image(record, sensor) for record in records)
        video = self.writer.write_camera(sensor.channel, images, self._frame_rate(records))

        sensor.camera.video = video
        for frame_index, record in enumerate(records):
            record.filename = video["path"]
            record.frame_index = frame_index
            record.fileformat = "av1_mp4"

    def copy_images(self, sensor: Sensor) -> None:
        """Copy the image files of a camera channel as they are, instead of encoding a video.

        Args:
            sensor (Sensor): Camera sensor with frames.
        """
        records = self._channel_frames(sensor)
        self._relink(sensor, records)
        for record in records:
            self.writer.copy(osp.join(self.data_root, record.filename), record.filename)

    def migrate(self, dataset_id: str, version: int, *, keep_images: bool = False) -> Manifest:
        """Migrate every channel, copy `map/` and `input_bag/`, then write the tables and
        `manifest.json`.

        Args:
            dataset_id (str): Dataset ID, as in the output folder.
            version (int): Dataset version, as in the output folder (given by Web.Auto).
            keep_images (bool, optional): Copy camera images as they are instead of encoding
                one video per channel.

        Returns:
            The manifest written.
        """
        for sensor in self.lidars():
            self.migrate_lidar(sensor)
        for sensor in self.cameras():
            if keep_images:
                self.copy_images(sensor)
            else:
                self.migrate_camera(sensor)
        for directory in ("map", "input_bag"):
            if osp.isdir(osp.join(self.data_root, directory)):
                self.writer.copy(osp.join(self.data_root, directory), directory)
        return self.writer.save(self.dataset.tables, self._manifest_info(dataset_id, version))

    def tables(self, table: SchemaName) -> list[Any]:
        """Return the 1.0 records of a table."""
        return self.dataset.tables[table]

    def _manifest_info(self, dataset_id: str, version: int) -> dict[str, Any]:
        """Return the manifest fields the writer does not compute. 0.x has no provenance, so
        it is left empty for backfilling, except the recording time (from the samples)."""
        timestamps = [sample.timestamp for sample in self.tables(SchemaName.SAMPLE)]
        self.notes.append(
            "provenance.rosbag.record_start / record_end are the first / last sample times"
        )

        def utc(timestamp: int) -> str:
            return datetime.fromtimestamp(timestamp / 1e6, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        return {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "version": version,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generators": [],
            "annotation_specifications": {},
            "provenance": {
                "rosbag": {
                    "log_file_ids": [],
                    "storage": None,
                    "record_start": utc(min(timestamps)),
                    "record_end": utc(max(timestamps)),
                },
                "topics": {},
                "process_config_id": None,
                "process_config_version_id": None,
            },
            "project_id": None,
            "source_project_id": None,
            "is_synthetic": False,
            "is_discontinuous": None,
            "migrated_from_schema_version": "0.x",
            "migration_notes": self.notes,
        }

    def _channel_frames(self, sensor: Sensor) -> list[SampleData]:
        """Return the frames of a sensor in timestamp order."""
        return sorted(
            (
                frame
                for frame in self.tables(SchemaName.SAMPLE_DATA)
                if frame.sensor_token == sensor.token
            ),
            key=lambda frame: frame.timestamp,
        )

    def _relink(self, sensor: Sensor, records: list[SampleData]) -> None:
        """Set `next` / `prev` of a channel's frames from their timestamp order.

        Some 0.x datasets leave a placeholder frame (`is_valid: false`) half linked: it points
        to its neighbors, but they point to each other. Each change is noted.
        """
        relinked = 0
        for i, record in enumerate(records):
            prev = records[i - 1].token if i > 0 else None
            next_ = records[i + 1].token if i + 1 < len(records) else None
            if (record.prev, record.next) != (prev, next_):
                record.prev, record.next = prev, next_
                relinked += 1
        if relinked:
            self.notes.append(
                f"{sensor.channel}: next / prev relinked in time order on {relinked} frames"
            )

    @staticmethod
    def _frame_rate(records: list[SampleData]) -> int:
        """Return the frame rate of a channel: the median interval between frames, in Hz."""
        if len(records) < 2:
            return 10  # one frame: any rate plays it
        interval = np.median(np.diff([record.timestamp for record in records]))
        return max(1, round(1_000_000 / interval))

    def _image(self, record: SampleData, sensor: Sensor) -> np.ndarray:
        image = load_image(osp.join(self.data_root, record.filename))
        if image.shape[:2] != (sensor.camera.height, sensor.camera.width):
            raise ValueError(
                f"{record.filename}: {image.shape[1]}x{image.shape[0]}, but {sensor.channel} is "
                f"{sensor.camera.width}x{sensor.camera.height}"
            )
        return image

    def _point_fields(
        self, channel: str, records: list[SampleData], source_fields: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        """Return the 1.0 point fields of a channel, from the values of all its frames.

        A field gets its 1.0 dtype when every value fits it, and keeps its 0.x dtype otherwise
        (with a warning). The ring (`channel`) is dropped when it is -1 on every point.
        """
        # 1.0 dtypes of the 0.x point fields (Autoware layout); other fields keep their dtype
        dtypes = {
            "x": "float32",
            "y": "float32",
            "z": "float32",
            "intensity": "uint8",
            "channel": "uint16",
            "return_type": "uint8",
            "time_stamp": "uint32",
        }

        # Over every frame: each field's smallest and largest value, and whether all its
        # values are whole numbers.
        low = {name: np.inf for name, _ in source_fields}
        high = {name: -np.inf for name, _ in source_fields}
        whole = {name: True for name, _ in source_fields}
        for record in records:
            for name, values in self._read_points(record, source_fields).items():
                if len(values) == 0:
                    continue
                low[name] = min(low[name], values.min())
                high[name] = max(high[name], values.max())
                whole[name] = whole[name] and np.array_equal(values, np.round(values))

        # Decide each field.
        fields = []
        for name, dtype in source_fields:
            target = np.dtype(dtypes.get(name, dtype))

            # Ring not recorded: the 0.x converter writes -1 on every point.
            if name == "channel" and low[name] == high[name] == -1:
                self.notes.append(f"{channel}: '{name}' dropped, -1 on every point (not recorded)")
                continue

            # Integer target: values must be whole and in range. Float target: always fits.
            no_points = low[name] > high[name]
            fits = (
                not np.issubdtype(target, np.integer)
                or no_points
                or (
                    whole[name]
                    and np.iinfo(target).min <= low[name]
                    and high[name] <= np.iinfo(target).max
                )
            )
            if fits:
                fields.append((name, target.name))
                continue

            # Keep the 0.x dtype (lossless) if it doesn't fit, warn.
            note = (
                f"{channel}: '{name}' kept as {dtype}, values in [{low[name]}, {high[name]}] "
                f"do not fit {target.name}"
            )
            warnings.warn(note)
            self.notes.append(note)
            fields.append((name, dtype))
        return fields

    def _lidar_frame(
        self,
        record: SampleData,
        source_fields: list[tuple[str, str]],
        fields: list[tuple[str, str]],
    ) -> dict[str, np.ndarray | None]:
        """Return one frame in the 1.0 layout, and set its `num_points`."""
        points = self._read_points(record, source_fields)
        frame = {name: points[name].astype(dtype) for name, dtype in fields if name in points}
        num_points = len(points[source_fields[0][0]])
        record.num_points = num_points

        info_filename = self._v0_frames[record.token].get("info_filename")
        if info_filename:
            frame |= self._sources(load_json(osp.join(self.data_root, info_filename)), num_points)
        if ("label", "uint8") in fields:
            labels = self._labels.get(record.token)
            if labels is None:
                frame["label"] = frame["instance"] = None
            else:
                label = np.fromfile(osp.join(self.data_root, labels), dtype=np.uint8)
                if len(label) != num_points:
                    raise ValueError(f"{labels}: {len(label)} labels for {num_points} points")
                frame["label"] = label
                frame["instance"] = np.zeros(num_points, dtype=np.uint32)
        return frame

    def _sources(self, info: dict, num_points: int) -> dict[str, np.ndarray]:
        """Return `source_index` (the source's `sensor.index`) and `source_timestamp` (µs)."""
        source_index = np.zeros(num_points, dtype=np.uint8)
        source_timestamp = np.zeros(num_points, dtype=np.int64)
        covered = np.zeros(num_points, dtype=bool)
        for source in info.get("sources", []):
            span = slice(source["idx_begin"], source["idx_begin"] + source["length"])
            source_index[span] = self._sensor_indices[self._v0_channels[source["sensor_token"]]]
            stamp = source["stamp"]
            source_timestamp[span] = stamp["sec"] * 1_000_000 + stamp["nanosec"] // 1000
            covered[span] = True
        if not covered.all():
            raise ValueError(f"{(~covered).sum()} points are outside the .info sources")
        return {"source_index": source_index, "source_timestamp": source_timestamp}

    def _source_fields(self, record: SampleData) -> list[tuple[str, str]]:
        """Return the 0.x point fields of a channel, from its first frame."""
        if record.filename.endswith(".pcd"):
            points = load_pointcloud(osp.join(self.data_root, record.filename))
            return [(name, values.dtype.name) for name, values in points.items()]
        info_filename = self._v0_frames[record.token].get("info_filename")
        info = load_json(osp.join(self.data_root, info_filename)) if info_filename else {}
        return [(name, "float32") for name in V0_BIN_FIELDS[: info.get("num_pts_feats", 5)]]

    def _read_points(
        self, record: SampleData, source_fields: list[tuple[str, str]]
    ) -> dict[str, np.ndarray]:
        filepath = osp.join(self.data_root, record.filename)
        if filepath.endswith(".pcd"):
            return load_pointcloud(filepath)
        return load_pointcloud(filepath, fields=source_fields)

    def _index_instances(self) -> None:
        """Give instances without `index` one from 1, as point labels require.

        0.x labels points by category only, so the `instance` column is 0 (no object), but
        `REC011` still asks every instance of an `is_thing` category for an index.
        """
        instances = self.tables(SchemaName.INSTANCE)
        if all(instance.index is not None for instance in instances):
            return
        for index, instance in enumerate(instances, start=1):
            instance.index = index
        self.notes.append(f"instance.index set from 1 on {len(instances)} instances (0.x has none)")

    def _check_unpainted(self) -> None:
        if not any(
            category.index == 0 and category.name == "unpainted"
            for category in self.tables(SchemaName.CATEGORY)
        ):
            raise ValueError("lidarseg is present, but category index 0 is not 'unpainted'")

    def _load_v0(self, table: str) -> list[dict]:
        """Return the raw records of a 0.x table, or [] if it is absent."""
        filepath = osp.join(self.data_root, "annotation", f"{table}.json")
        return load_json(filepath) if osp.exists(filepath) else []
