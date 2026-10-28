from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

import pyarrow as pa
import pyarrow.parquet as pq

from t4_devkit.sanity import sanity_check

SAMPLE_ROOT = Path(__file__).parent / "sample"
SAMPLE_V0 = SAMPLE_ROOT / "t4dataset"
SAMPLE_V1 = SAMPLE_ROOT / "t4dataset_v1"


class SampleCopy:
    """A writable copy of a sample dataset, for tests that change or break it.

    Examples:
        >>> sample = SampleCopy(tmp_path)  # the 1.0 sample, as `<tmp_path>/sample`
        >>> sample.edit("scene", lambda records: SampleCopy.set_field(records, 0, nbr_samples=5))
        >>> sample.reports()["REC012"].is_failed()
        True
    """

    def __init__(self, tmp_path: Path, source: Path = SAMPLE_V1, name: str = "sample") -> None:
        """
        Args:
            tmp_path (Path): Directory to copy into.
            source (Path, optional): Sample to copy, the 1.0 sample by default.
            name (str, optional): Folder name; "sample" is the 1.0 sample's `dataset_id`.
        """
        self.root = tmp_path / name
        shutil.copytree(source, self.root)

    def read(self, table: str) -> Any:
        """Return a table (or "manifest") as stored."""
        return json.loads(self._path(table).read_text())

    def edit(self, table: str, change: Callable[[Any], Any]) -> None:
        """Replace a table (or "manifest") with `change(records)`."""
        self._path(table).write_text(json.dumps(change(self.read(table))))

    def reports(self, **kwargs: Any) -> dict[str, Any]:
        """Return the sanity reports by rule ID; `kwargs` go to `sanity_check`."""
        result = sanity_check(self.root.as_posix(), **kwargs)
        return {report.id: report for report in result.reports}

    def write_labels(self, frames: list[list[int | None] | None]) -> None:
        """Add a `label` column to the 1.0 sample's LiDAR file and to its `sensor.json` fields.

        Args:
            frames (list[list[int | None] | None]): Labels per frame; None for a frame without
                labels.
        """
        path = self.root / "data/LIDAR_TOP/LIDAR_TOP.parquet"
        parquet = pq.ParquetFile(path)
        schema = parquet.schema_arrow.append(pa.field("label", pa.uint8()))
        with pq.ParquetWriter(path.with_suffix(".tmp"), schema) as writer:
            for i, labels in enumerate(frames):
                table = parquet.read_row_group(i)
                column = (
                    pa.nulls(table.num_rows, pa.uint8())
                    if labels is None
                    else pa.array(labels, pa.uint8())
                )
                writer.write_table(table.append_column("label", column))
        path.with_suffix(".tmp").replace(path)

        def declare(records: list[dict]) -> list[dict]:
            records[1]["lidar"]["fields"].append({"name": "label", "dtype": "uint8"})
            return records

        self.edit("sensor", declare)

    @staticmethod
    def set_field(records: list[dict], position: int, **fields: Any) -> list[dict]:
        """Return the records with `fields` set on the record at `position`."""
        records[position].update(fields)
        return records

    def _path(self, table: str) -> Path:
        if table == "manifest":
            return self.root / "manifest.json"
        return self.root / "annotation" / f"{table}.json"
