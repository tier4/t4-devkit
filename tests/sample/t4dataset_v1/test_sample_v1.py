from __future__ import annotations

import hashlib
import json
from pathlib import Path

SAMPLE_V1 = Path(__file__).parent


def test_sample_v1_manifest_matches_files() -> None:
    """Every table and asset listed in manifest.json exists and has the listed hash."""
    manifest = json.loads((SAMPLE_V1 / "manifest.json").read_text())
    assert manifest["schema_version"] == "1.0.0"

    for entry in [*manifest["tables"].values(), *manifest["assets"]]:
        data = (SAMPLE_V1 / entry["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]
        if "bytes" in entry:
            assert len(data) == entry["bytes"], entry["path"]
