from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from t4_devkit.cli.migrate import cli

SAMPLE_V0 = Path(__file__).parents[1] / "sample" / "t4dataset"


def test_t4migrate(tmp_path: Path) -> None:
    """The 0.x sample migrates to <output>/<DATASET_ID>/<DATASET_VERSION> and passes sanity."""
    with pytest.warns(UserWarning, match="kept as float32"):
        result = CliRunner().invoke(cli, [SAMPLE_V0.as_posix(), tmp_path.as_posix(), "-d", "3"])

    assert result.exit_code == 0, result.output  # t4migrate exits 1 if a sanity rule fails
    manifest = json.loads((tmp_path / "t4dataset" / "3" / "manifest.json").read_text())
    assert (manifest["dataset_id"], manifest["version"]) == ("t4dataset", 3)
    assert manifest["migrated_from_schema_version"] == "0.x"
    assert {asset["path"] for asset in manifest["assets"]} >= {
        "data/LIDAR_TOP/LIDAR_TOP.parquet",
        "data/CAM_FRONT/CAM_FRONT.mp4",
        "map/lanelet2_map.osm",
    }
