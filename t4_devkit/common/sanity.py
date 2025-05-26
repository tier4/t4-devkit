from __future__ import annotations

import re
import warnings
from pathlib import Path

from attrs import define

from t4_devkit import Tier4

__all__ = ["DBException", "sanity_check"]


@define
class DBException:
    """A dataclass to store error message of the corresponding dataset."""

    dataset_id: str
    version: str | None
    message: str


def sanity_check(db_root: str | Path, *, include_warning: bool = False) -> DBException | None:
    """Perform sanity check and report exception or warning encountered while loading the dataset.

    Args:
        db_root (str | Path): Path to root directory of the dataset.
        include_warning (bool, optional): Indicates whether to report warnings.

    Returns:
        Exception or warning if exits, otherwise returns None.
    """
    db_root_path = Path(db_root)

    version_pattern = re.compile(r".*/\d+$")
    versions = [d.name for d in db_root_path.iterdir() if version_pattern.match(str(d))]

    if versions:
        version = sorted(versions)[-1]
        data_root = db_root_path.joinpath(version).as_posix()
    else:
        version = None
        data_root = db_root_path.as_posix()

    with warnings.catch_warnings():
        if include_warning:
            warnings.filterwarnings("error")
        else:
            warnings.filterwarnings("ignore")

        try:
            _ = Tier4("annotation", data_root=data_root, verbose=False)
            exception = None
        except Exception as e:
            exception = DBException(
                dataset_id=db_root_path.name,
                version=version,
                message=str(e),
            )
    return exception
