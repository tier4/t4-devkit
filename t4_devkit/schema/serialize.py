from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.common.serialize import serialize_dataclass

if TYPE_CHECKING:
    from .tables import SchemaTable


__all__ = ("serialize_schemas", "serialize_schema")


def serialize_schemas(data: list[SchemaTable]) -> list[dict]:
    """Serialize a list of schema dataclasses into list of dict.

    Args:
        data (list[SchemaTable]): List of schema dataclasses.

    Returns:
        Serialized list of dict data.
    """
    return [serialize_schema(d) for d in data]


def serialize_schema(data: SchemaTable) -> dict:
    """Serialize a schema dataclass into dict.

    Args:
        data (SchemaTable): Schema dataclass.

    Returns:
        Serialized dict data.
    """
    return serialize_dataclass(data)
