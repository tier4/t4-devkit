from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .files import lidar_column_values

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF305"]


@CHECKERS.register()
class REF305(RecordsChecker):
    """A checker of REF305."""

    id = RuleID("REF305")
    name = RuleName("lidar-source-index")
    severity = Severity.ERROR
    description = (
        "In a merged LiDAR file, 'source_index' values are the 'Sensor.index' of the channel's "
        "'source_channels'."
    )
    tables = (SchemaName.SENSOR,)

    def check(self, context: SanityContext) -> list[Reason] | None:
        sensors = context.load_records(SchemaName.SENSOR).unwrap()
        data_root = context.data_root.unwrap()
        failures = []
        for sensor in sensors:
            if sensor.lidar is None or not sensor.lidar.source_channels:
                continue
            path = sensor.lidar.container.path
            if path is None or not data_root.joinpath(path).exists():
                continue
            expected = {s.index for s in sensors if s.channel in sensor.lidar.source_channels}
            values = lidar_column_values(data_root.joinpath(path), "source_index")
            if values is None:
                failures.append(Reason(f"Sensor {sensor.channel}: no 'source_index' column"))
            elif not values <= expected:
                failures.append(
                    Reason(
                        f"Sensor {sensor.channel}: 'source_index' values {sorted(values - expected)} are not its sources"
                    )
                )
        return failures or None
