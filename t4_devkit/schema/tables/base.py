from __future__ import annotations

from abc import ABC
from typing import Any, TypeVar

from attrs import define

from t4_devkit.common.io import load_json

__all__ = ["SchemaBase", "SchemaTable"]


@define
class SchemaBase(ABC):
    """Abstract base dataclass of schema tables."""

    token: str

    @staticmethod
    def shortcuts() -> tuple[str, ...] | None:
        """Return a sequence of shortcut field names.

        Returns:
            Returns None if there is no shortcut. Otherwise, returns sequence of shortcut field names.
        """
        return None

    @classmethod
    def from_json(cls, filepath: str) -> list[SchemaTable]:
        """Construct dataclass from json file.

        Args:
            filepath (str): Filepath to json.

        Returns:
            List of instantiated schema dataclasses.
        """
        records: list[dict[str, Any]] = load_json(filepath)
        return [cls.from_dict(data) for data in records]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchemaTable:
        """Construct dataclass from dict.

        Args:
            data (dict[str, Any]): Dict data.

        Returns:
            Instantiated schema dataclass.
        """
        return cls(**data)


SchemaTable = TypeVar("SchemaTable", bound=SchemaBase)
