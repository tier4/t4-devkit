from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np
from attrs import asdict, filters
from pyquaternion import Quaternion

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
    excludes = filters.exclude(*data.shortcuts()) if data.shortcuts() is not None else None
    return asdict(data, filter=excludes, value_serializer=_value_serializer)


def _value_serializer(data: SchemaTable, attr: Any, value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, Quaternion):
        return value.q.tolist()
    elif isinstance(value, Enum):
        return value.value
    return value
