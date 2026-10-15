from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .files import describe_lidar_file, describe_video_file

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF205"]


@CHECKERS.register()
class REF205(RecordsChecker):
    """A checker of REF205."""

    id = RuleID("REF205")
    name = RuleName("sensor-file-description")
    severity = Severity.ERROR
    description = (
        "Each channel file matches its 'sensor' row: Parquet columns, dtypes and one row group per "
        "frame; video codec, pixel format, bit depth, timescale, frame count and frame size."
    )
    tables = (SchemaName.SENSOR,)

    def check(self, context: SanityContext) -> list[Reason] | None:
        data_root = context.data_root.unwrap()
        failures = []
        for sensor in context.load_records(SchemaName.SENSOR).unwrap():
            if sensor.camera is not None and sensor.camera.video is not None:
                path = data_root.joinpath(sensor.camera.video.path)
                if path.exists():
                    failures += describe_video_file(sensor, path)
            elif sensor.lidar is not None and sensor.lidar.container.path is not None:
                path = data_root.joinpath(sensor.lidar.container.path)
                if path.exists() and sensor.lidar.container.format.value == "parquet":
                    failures += describe_lidar_file(sensor, path)
        return failures or None
