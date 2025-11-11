from __future__ import annotations

from returns.result import Result, safe

from t4_devkit.common.io import load_json
from t4_devkit import Tier4


@safe
def load_json_safe(filename: str) -> Result[list[dict], Exception]:
    """Load JSON file safely."""
    return load_json(filename)


@safe
def init_tier4_safe(data_root: str, revision: str | None = None) -> Result[Tier4, Exception]:
    """Initialize Tier4 instance safely."""
    return Tier4(data_root, revision=revision, verbose=False)
