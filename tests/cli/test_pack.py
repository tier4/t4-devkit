from __future__ import annotations

from pathlib import Path

import numpy as np
from typer.testing import CliRunner

from t4_devkit.cli.pack import cli


def _create_dataset(tmp_path: Path) -> Path:
    data_root = tmp_path / "dataset_id"
    lidar_dir = data_root / "0" / "data" / "LIDAR_CONCAT"
    lidar_dir.mkdir(parents=True)
    (data_root / "0" / "data" / "CAM_FRONT").mkdir()
    for i in range(3):
        frame = np.zeros((10, 5), dtype=np.float32)
        frame[:, :3] = i
        frame.tofile(lidar_dir / f"{i:05d}.pcd.bin")
    return data_root


def test_pack_and_verify(tmp_path: Path) -> None:
    data_root = _create_dataset(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["pack", str(data_root), "--level", "1"])
    assert result.exit_code == 0, result.output
    assert "PACKED" in result.output
    assert (data_root / "0" / "data" / "LIDAR_CONCAT.pack").exists()
    assert not (data_root / "0" / "data" / "CAM_FRONT.pack").exists()

    result = runner.invoke(cli, ["pack", str(data_root)])
    assert result.exit_code == 0, result.output
    assert "SKIP" in result.output

    result = runner.invoke(cli, ["verify", str(data_root)])
    assert result.exit_code == 0, result.output
    assert "VERIFIED" in result.output


def test_verify_fails_on_changed_frame(tmp_path: Path) -> None:
    data_root = _create_dataset(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["pack", str(data_root), "--level", "1"])

    np.ones((10, 5), dtype=np.float32).tofile(
        data_root / "0" / "data" / "LIDAR_CONCAT" / "00001.pcd.bin"
    )

    result = runner.invoke(cli, ["verify", str(data_root)])
    assert result.exit_code == 1
    assert "FAILED" in result.output


def test_verify_fails_without_pack(tmp_path: Path) -> None:
    data_root = _create_dataset(tmp_path)

    result = CliRunner().invoke(cli, ["verify", str(data_root)])

    assert result.exit_code == 1
