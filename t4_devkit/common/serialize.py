from __future__ import annotations

from enum import Enum
from typing import Any

import numpy as np
from attrs import asdict, fields, filters
from pyquaternion import Quaternion


def serialize_dataclass(data: Any) -> dict[str, Any]:
    """Serialize attrs' dataclasses into dict.

    Note that all fields specified with `init=False` will be skipped to be serialized.

    Args:
        data (Any): Dataclass object.

    Returns:
        dict[str, Any]: Serialized dict.
    """
    excludes = filters.exclude(*[a for a in fields(data.__class__) if not a.init])
    return asdict(data, filter=excludes, value_serializer=_value_serializer)


def _value_serializer(data: Any, attribute: Any, value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, Quaternion):
        return value.q.tolist()
    elif isinstance(value, tuple):
        return list(value)
    elif isinstance(value, Enum):
        return value.value
    return value
