from __future__ import annotations

import warnings
from enum import Enum, unique
from pathlib import Path

from attrs import define, field

from t4_devkit import load_metadata, load_table
from t4_devkit.schema import SchemaName

__all__ = ["DBException", "sanity_check"]


@define
class DBException:
    """A dataclass to store error message of the corresponding dataset.

    Attributes:
        dataset_id (str): Dataset ID.
        version (str | None): Dataset version.
        messages (list[ExceptionMessage]): Error or warning messages.
    """

    dataset_id: str
    version: str | None
    messages: list[ExceptionMessage] = field(factory=list, init=False)

    def add_message(self, message: ExceptionMessage) -> None:
        self.messages.append(message)

    def is_ok(self) -> bool:
        """Return True if the status is OK."""
        return all(m.is_ok() for m in self.messages)

    @property
    def status(self) -> DBStatus:
        if self.is_ok():
            return DBStatus.OK
        elif any(m.status == DBStatus.ERROR for m in self.messages):
            return DBStatus.ERROR
        else:
            return DBStatus.WARNING


@define
class ExceptionMessage:
    name: str
    status: DBStatus
    message: str

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

        metadata = load_metadata(db_root)
        exception = DBException(dataset_id=metadata.dataset_id, version=metadata.version)
        for schema in SchemaName:
            try:
                _ = load_table(metadata, schema)
            except Warning as w:
                exception.add_message(
                    ExceptionMessage(name=schema.name, status=DBStatus.WARNING, message=str(w))
                )
            except Exception as e:
                exception.add_message(
                    ExceptionMessage(name=schema.name, status=DBStatus.ERROR, message=str(e))
                )

    return exception
