from __future__ import annotations

from pathlib import Path

import make_sample_v1

SAMPLE_V1 = Path(__file__).parent


def test_generator_reproduces_sample(tmp_path: Path) -> None:
    """`make_sample_v1.py` writes the committed sample: run it after changing either.

    The video and the manifest (its hash and the t4-devkit version) are left out: their bytes
    depend on the encoder build and the installed version.
    """
    make_sample_v1.write(tmp_path / "sample")
    paths = [
        *(f"annotation/{path.name}" for path in (SAMPLE_V1 / "annotation").glob("*.json")),
        "data/LIDAR_TOP/LIDAR_TOP.parquet",
        "map/lanelet2_map.osm",
    ]
    for path in paths:
        assert (tmp_path / "sample" / path).read_bytes() == (SAMPLE_V1 / path).read_bytes(), path
