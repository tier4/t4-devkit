from __future__ import annotations

import json
from typing import Any

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = ("load_json", "save_json")


def load_json(filename: PathLike) -> Any:
    """Load json data from specified filepath.

    Args:
        filename (PathLike): File path to .json file.

    Returns:
        Loaded data.
    """
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def save_json(data: Any, filename: PathLike) -> None:
    """Save data into json file.

    Args:
        data (Any): Data to be saved.
        filename (PathLike): File path to save as json.
    """
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
