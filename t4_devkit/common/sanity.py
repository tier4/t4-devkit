from __future__ import annotations

import warnings
from pathlib import Path

from attrs import define

from t4_devkit import Tier4, load_metadata

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

    with warnings.catch_warnings():
        if include_warning:
            warnings.filterwarnings("error")
        else:
            warnings.filterwarnings("ignore")

        try:
            _ = Tier4(data_root=db_root, verbose=False)
            exception = None
        except Exception as e:
            metadata = load_metadata(db_root)

            exception = DBException(
                dataset_id=metadata.dataset_id,
                version=metadata.version,
                message=str(e),
            )
    return exception
