from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful

from t4_devkit.schema import SchemaName, SensorModality
from t4_devkit.schema.v1 import FileFormat, LidarContainerFormat, Task
from t4_devkit.schema.v1 import SchemaName as V1SchemaName

from ..checker import Checker
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from t4_devkit.schema.v1 import Sensor

    from ..context import SanityContext


class RecordCountChecker(Checker):
    """Base class for record count checkers.

    Attributes:
        id (RuleID): The ID of the rule.
        name (RuleName): The name of the rule.
        severity (Severity): The severity of the rule.
        description (str): The description of the rule.
        schema (SchemaName): The schema name to check.
    """

    schema: SchemaName

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match context.to_schema_file(self.schema):
            case Some(x):
                if not x.exists():
                    return Maybe.from_value(Reason(f"Missing {self.schema.filename}"))
                elif not is_successful(load_json_safe(x)):
                    return Maybe.from_value(Reason(f"Cannot read {self.schema.filename}"))
                else:
                    return Nothing
            case _:
                return Maybe.from_value(Reason("Missing 'annotation' directory path"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        filepath = context.to_schema_file(self.schema).unwrap()
        records = load_json_safe(filepath).unwrap()
        return self.check_count(records)

    @abstractmethod
    def check_count(self, records: list[dict]) -> list[Reason] | None:
        """Check the count of records.

        Args:
            records (list[dict]): The list of records to check.

        Returns:
            A list of reasons for any issues found, otherwise None.
        """
        pass


def channel_file(sensor: Sensor) -> tuple[str, int] | None:
    """Return the file and frame count of a channel stored in one file, or None for one file per
    frame."""
    if sensor.camera is not None and sensor.camera.video is not None:
        return sensor.camera.video.path, sensor.camera.video.frame_count
    if sensor.lidar is not None and sensor.lidar.container.path is not None:
        return sensor.lidar.container.path, sensor.lidar.container.frame_count
    return None


# `sample_data.fileformat` values for each LiDAR container format.
LIDAR_FRAME_FORMATS = {
    LidarContainerFormat.PARQUET: {FileFormat.PARQUET.value},
    LidarContainerFormat.PCD: {FileFormat.PCD.value},
    LidarContainerFormat.BIN: {FileFormat.BIN.value, FileFormat.PCDBIN.value},
}


def frame_formats(sensor: Sensor) -> set[str]:
    """Return the `sample_data.fileformat` values a sensor's storage allows (any for radar,
    undefined in 1.0)."""
    if sensor.camera is not None:
        if sensor.camera.video is not None:
            return {FileFormat.AV1_MP4.value}
        return {FileFormat.JPG.value, FileFormat.PNG.value}
    if sensor.lidar is not None:
        return LIDAR_FRAME_FORMATS[sensor.lidar.container.format]
    return {fileformat.value for fileformat in FileFormat}


# Tasks whose labels are checked against `capabilities.tasks`.
CHECKED_TASKS = (
    Task.DETECTION3D,
    Task.DETECTION2D,
    Task.SEGMENTATION2D,
    Task.SEGMENTATION3D,
    Task.KEYPOINT,
    Task.TRAFFIC_LIGHT,
)


def declared_capabilities(context: SanityContext) -> set[str]:
    """Return what `manifest.json` `capabilities` declares, as items like "camera:CAM_FRONT", "map",
    "task:detection3d"."""
    capabilities = context.manifest.unwrap().capabilities
    items = {
        f"{modality}:{channel}"
        for modality in ("camera", "lidar", "radar")
        for channel in getattr(capabilities.modalities, modality)
    }
    items |= {
        name
        for name in ("map", "route", "traffic_light", "vehicle_state", "scenario")
        if getattr(capabilities, name)
    }
    items |= {f"task:{task.value}" for task in capabilities.tasks if task in CHECKED_TASKS}
    return items


def present_capabilities(context: SanityContext) -> set[str]:
    """Return what the dataset contains, as the same items as `declared_capabilities`."""

    def records(table: V1SchemaName) -> list:
        return context.load_records(table).unwrap()

    sensors = records(V1SchemaName.SENSOR)
    with_frames = {frame.sensor_token for frame in records(V1SchemaName.SAMPLE_DATA)}
    items = {
        f"{sensor.modality.value}:{sensor.channel}"
        for sensor in sensors
        if sensor.token in with_frames
    }
    tables = {
        "map": V1SchemaName.MAP,
        "route": V1SchemaName.ROUTE,
        "traffic_light": V1SchemaName.TRAFFIC_LIGHT,
        "vehicle_state": V1SchemaName.VEHICLE_STATE,
        "scenario": V1SchemaName.SCENARIO,
    }
    items |= {name for name, table in tables.items() if records(table)}

    things = {category.token for category in records(V1SchemaName.CATEGORY) if category.is_thing}
    object_anns = records(V1SchemaName.OBJECT_ANN)
    lidar_columns = {
        field.name
        for sensor in sensors
        if sensor.modality == SensorModality.LIDAR and sensor.lidar is not None
        for field in sensor.lidar.fields
    }
    tasks = {
        Task.DETECTION3D: bool(records(V1SchemaName.SAMPLE_ANNOTATION)),
        Task.DETECTION2D: any(ann.category_token in things for ann in object_anns),
        Task.SEGMENTATION2D: any(ann.mask is not None for ann in object_anns),
        Task.SEGMENTATION3D: "label" in lidar_columns,
        Task.KEYPOINT: bool(records(V1SchemaName.KEYPOINT)),
        Task.TRAFFIC_LIGHT: bool(records(V1SchemaName.TRAFFIC_LIGHT))
        or any(instance.map_element.id is not None for instance in records(V1SchemaName.INSTANCE)),
    }
    items |= {f"task:{task.value}" for task, present in tasks.items() if present}
    return items
