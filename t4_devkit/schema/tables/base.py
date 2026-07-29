from __future__ import annotations

from abc import ABC
from secrets import token_hex
from typing import Any, Sized, TypeVar

from attrs import define, field, validators
from typing_extensions import TYPE_CHECKING

from t4_devkit.common.io import load_json

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = ["SchemaBase", "SchemaTable"]


def impossible_empty():
    """Factory function that returns a validator instance which raises ValueError if value is empty."""
    return _ImpossibleEmptyValidator()


@define(slots=True, unsafe_hash=True)
class _ImpossibleEmptyValidator:
    def __call__(self, instance, attribute, value: Sized) -> None:
        if len(value) == 0:
            raise ValueError(f"{attribute.name} cannot be empty")


@define
class SchemaBase(ABC):
    """Abstract base dataclass of schema tables."""

    token: str = field(validator=(validators.instance_of(str), impossible_empty()))

    @classmethod
    def from_json(cls, filepath: PathLike) -> list[SchemaTable]:
        """Construct dataclass from json file.

        Args:
            filepath (PathLike): Filepath to json.

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

    @classmethod
    def new(cls, data: dict[str, Any], *, token_nbytes: int = 16) -> SchemaTable:
        """Create a new schema instance generating random token.

        Args:
            data (dict[str, Any]): Schema field data without token.
            token_nbytes (int, optional): The number of bytes of a new token.

        Returns:
            Schema instance with a new token.
        """
        new_data = data.copy()

        token = token_hex(nbytes=token_nbytes)
        new_data["token"] = token

        return cls.from_dict(new_data)


SchemaTable = TypeVar("SchemaTable", bound=SchemaBase)
