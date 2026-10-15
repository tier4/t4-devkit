from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .files import lidar_column_values

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF306"]


@CHECKERS.register()
class REF306(RecordsChecker):
    """A checker of REF306."""

    id = RuleID("REF306")
    name = RuleName("lidar-point-labels")
    severity = Severity.ERROR
    description = (
        "In a LiDAR file, 'label' values are 'Category.index' values, and 'instance' values are "
        "'Instance.index' values or 0 (no object)."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.CATEGORY,
        SchemaName.INSTANCE,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        data_root = context.data_root.unwrap()
        indices = {
            "label": {c.index for c in context.load_records(SchemaName.CATEGORY).unwrap()},
            "instance": {0} | {i.index for i in context.load_records(SchemaName.INSTANCE).unwrap()},
        }
        failures = []
        for sensor in context.load_records(SchemaName.SENSOR).unwrap():
            if sensor.lidar is None or sensor.lidar.container.path is None:
                continue
            path = data_root.joinpath(sensor.lidar.container.path)
            if not path.exists():
                continue
            for column, known in indices.items():
                values = lidar_column_values(path, column)
                if values is not None and not values <= known:
                    failures.append(
                        Reason(
                            f"Sensor {sensor.channel}: '{column}' values {sorted(values - known)} not defined"
                        )
                    )
        return failures or None
