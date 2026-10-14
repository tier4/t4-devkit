from __future__ import annotations

from typing import TYPE_CHECKING

import pyarrow.parquet as pq

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from pathlib import Path

    from ..context import SanityContext


__all__ = ["REF206"]


@CHECKERS.register()
class REF206(RecordsChecker):
    """A checker of REF206."""

    id = RuleID("REF206")
    name = RuleName("lidar-num-points")
    severity = Severity.ERROR
    description = "'SampleData.num_points' equals the number of points in its frame, when set."
    tables = (
        SchemaName.SENSOR,
        SchemaName.SAMPLE_DATA,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        data_root = context.data_root.unwrap()
        files = {
            sensor.token: data_root.joinpath(sensor.lidar.container.path)
            for sensor in context.load_records(SchemaName.SENSOR).unwrap()
            if sensor.lidar is not None
            and sensor.lidar.container.path is not None
            and sensor.lidar.container.format.value == "parquet"
        }
        row_counts = {
            token: _row_group_sizes(path) for token, path in files.items() if path.exists()
        }
        failures = []
        for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap():
            counts = row_counts.get(frame.sensor_token)
            if counts is None or frame.num_points is None or frame.frame_index is None:
                continue
            if frame.frame_index >= len(counts) or counts[frame.frame_index] != frame.num_points:
                failures.append(
                    Reason(
                        f"SampleData {frame.token}: 'num_points' {frame.num_points} differs from its frame"
                    )
                )
        return failures or None


def _row_group_sizes(path: Path) -> list[int]:
    metadata = pq.ParquetFile(path).metadata
    return [metadata.row_group(i).num_rows for i in range(metadata.num_row_groups)]
