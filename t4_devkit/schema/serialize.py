from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import deprecated

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses

if TYPE_CHECKING:
    from .tables import SchemaTable


__all__ = ("serialize_schemas", "serialize_schema")


@deprecated("`serialize_schemas()` is deprecated. Please use `serialize_dataclasses()` instead.")
def serialize_schemas(data: list[SchemaTable]) -> list[dict]:
    """Serialize a list of schema dataclasses into list of dict.

    Deprecated:
        This function is deprecated. Please use `serialize_dataclasses()` instead.

    Args:
        data (list[SchemaTable]): List of schema dataclasses.

    Returns:
        Serialized list of dict data.
    """
    return serialize_dataclasses(data)


@deprecated("`serialize_schema()` is deprecated. Please use `serialize_dataclass()` instead.")
def serialize_schema(data: SchemaTable) -> dict:
    """Serialize a schema dataclass into dict.

    Deprecated:
        This function is deprecated. Please use `serialize_dataclass()` instead.

    Args:
        data (SchemaTable): Schema dataclass.

    Returns:
        Serialized dict data.
    """
    return serialize_dataclass(data)
