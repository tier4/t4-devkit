from __future__ import annotations

import warnings
from enum import Enum, unique
from pathlib import Path

from attrs import define

from t4_devkit import Tier4, load_metadata

__all__ = ["DBException", "sanity_check"]


@define
class DBException:
    """A dataclass to store error message of the corresponding dataset.

    Attributes:
        dataset_id (str): Dataset ID.
        version (str | None): Dataset version.
        status (DBStatus): Status of the dataset.
        message (str): Error or warning message.
    """

    dataset_id: str
    version: str | None
    status: DBStatus
    message: str | None = None

    def is_ok(self) -> bool:
        """Return True if the status is OK."""
        return self.status == DBStatus.OK


@unique
class DBStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


def sanity_check(
    db_root: str | Path,
    *,
    revision: str | None = None,
    include_warning: bool = False,
) -> DBException:
    """Perform sanity check and report exception or warning encountered while loading the dataset.

    Args:
        db_root (str | Path): Path to root directory of the dataset.
        revision (str | None, optional): Specific version of the dataset.
            If None, search the latest one.
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
            t4 = Tier4(data_root=db_root, revision=revision, verbose=False)
            exception = DBException(
                dataset_id=t4.dataset_id,
                version=t4.version,
                status=DBStatus.OK,
            )
        except Warning as w:
            metadata = load_metadata(db_root)

            exception = DBException(
                dataset_id=metadata.dataset_id,
                version=metadata.version,
                status=DBStatus.WARNING,
                message=str(w),
            )
        except Exception as e:
            metadata = load_metadata(db_root)

            exception = DBException(
                dataset_id=metadata.dataset_id,
                version=metadata.version,
                status=DBStatus.ERROR,
                message=str(e),
            )
    return exception
