from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..reference.files import lidar_partly_null_frames
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC029"]


@CHECKERS.register()
class REC029(RecordsChecker):
    """A checker of REC029."""

    id = RuleID("REC029")
    name = RuleName("point-labels-reserved")
    severity = Severity.ERROR
    description = (
        "When a LiDAR file has 'label' / 'instance' columns: the 'Category' with 'index' 0 is "
        "named 'unpainted', and each frame's label columns are null on all points or on none."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.CATEGORY,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        sensors = [s for s in context.load_records(SchemaName.SENSOR).unwrap() if s.lidar]
        columns = {field.name for sensor in sensors for field in sensor.lidar.fields}
        failures = []
        if "label" in columns:
            names = [
                c.name for c in context.load_records(SchemaName.CATEGORY).unwrap() if c.index == 0
            ]
            if not names:
                failures.append(Reason("No 'Category' with 'index' 0 ('unpainted')"))
            elif names != ["unpainted"]:
                failures.append(Reason(f"'Category' with 'index' 0 is {names}, not 'unpainted'"))

        data_root = context.data_root.unwrap()
        for sensor in sensors:
            if sensor.lidar.container.path is None:
                continue
            path = data_root.joinpath(sensor.lidar.container.path)
            if not path.exists():
                continue
            for column in ("label", "instance"):
                frames = lidar_partly_null_frames(path, column)
                if frames:
                    failures.append(
                        Reason(
                            f"Sensor {sensor.channel}: '{column}' is null on only some points of "
                            f"frames {frames[:10]}"
                        )
                    )
        return failures or None
