from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful

from t4_devkit.schema import SchemaName
from t4_devkit.schema.v1 import Capabilities, FileFormat, LidarContainerFormat
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


def frame_formats(sensor: Sensor) -> set[str]:
    """Return the `sample_data.fileformat` values a sensor's storage allows (any for radar,
    undefined in 1.0)."""
    if sensor.camera is not None:
        if sensor.camera.video is not None:
            return {FileFormat.AV1_MP4.value}
        return {FileFormat.JPG.value, FileFormat.PNG.value}
    if sensor.lidar is not None:
        lidar_formats = {
            LidarContainerFormat.PARQUET: {FileFormat.PARQUET.value},
            LidarContainerFormat.PCD: {FileFormat.PCD.value},
            LidarContainerFormat.BIN: {FileFormat.BIN.value, FileFormat.PCDBIN.value},
        }
        return lidar_formats[sensor.lidar.container.format]
    return {fileformat.value for fileformat in FileFormat}


def capability_items(capabilities: Capabilities) -> set[str]:
    """Return capabilities as comparable items, e.g. "camera:CAM_FRONT", "map", "task:keypoint"."""
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
    items |= {f"task:{task.value}" for task in capabilities.tasks}
    return items


def present_capabilities(context: SanityContext, tables: tuple[V1SchemaName, ...]) -> set[str]:
    """Return what the dataset's tables contain, as `capability_items`."""
    records = {table: context.load_records(table).unwrap() for table in tables}
    return capability_items(Capabilities.from_tables(records))
