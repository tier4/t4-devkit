from __future__ import annotations

import warnings
from enum import Enum, unique

from attrs import define, field, validators
from typing_extensions import Self

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ("Visibility", "VisibilityLevel")


@unique
class VisibilityLevel(str, Enum):
    """An enum to represent visibility levels.

    Attributes:
        FULL: No occlusion for the object.
        MOST: Object is occluded, but by less than 50%.
        PARTIAL: Object is occluded, but by more than 50%.
        NONE: Object is 90-100% occluded and no points/pixels are visible in the label.
        UNAVAILABLE: Visibility level is not specified.
    """

    FULL = "full"
    MOST = "most"
    PARTIAL = "partial"
    NONE = "none"
    UNAVAILABLE = "unavailable"

    @classmethod
    def from_value(cls, level: str) -> Self:
        """Load member from its value."""
        if level not in cls.__members__.values():
            return cls._from_alias(level)
        return cls(level)

    @staticmethod
    def _from_alias(level: str) -> Self:
        """Load member from alias format of level.

        Args:
            level (str): Level of visibility.
        """
        if level == "v0-40":
            return VisibilityLevel.NONE
        elif level == "v40-60":
            return VisibilityLevel.PARTIAL
        elif level == "v60-80":
            return VisibilityLevel.MOST
        elif level == "v80-100":
            return VisibilityLevel.FULL
        else:
            warnings.warn(
                f"level: {level} is not supported, Visibility.UNAVAILABLE will be assigned."
            )
            return VisibilityLevel.UNAVAILABLE

    def rank(self) -> int:
        """Return an integer rank for comparison (higher is more visible)."""
        ranking = {
            "full": 4,
            "most": 3,
            "partial": 2,
            "none": 1,
            "unavailable": None,
        }
        return ranking[self.value]

    def is_comparable(self) -> bool:
        """Return True if the visibility level has a defined rank."""
        return self.rank() is not None

    def _check_comparability(self, other: VisibilityLevel) -> None:
        if not (self.is_comparable() and other.is_comparable()):
            raise ValueError(f"Cannot compare unknown visibility levels: {self}, {other}")

    def __lt__(self, other: VisibilityLevel) -> bool:
        self._check_comparability(other)
        return self.rank() < other.rank()

    def __le__(self, other: VisibilityLevel) -> bool:
        self._check_comparability(other)
        return self.rank() <= other.rank()

    def __gt__(self, other: VisibilityLevel) -> bool:
        self._check_comparability(other)
        return self.rank() > other.rank()

    def __ge__(self, other: VisibilityLevel) -> bool:
        self._check_comparability(other)
        return self.rank() >= other.rank()


@define(slots=False)
@SCHEMAS.register(SchemaName.VISIBILITY)
class Visibility(SchemaBase):
    """A dataclass to represent schema table of `visibility.json`.

    Attributes:
        token (str): Unique record identifier.
        level (VisibilityLevel): Visibility level.
        description (str): Description of visibility level.
    """

    level: VisibilityLevel = field(
        converter=lambda x: VisibilityLevel.from_value(x)
        if not isinstance(x, VisibilityLevel)
        else VisibilityLevel(x)
    )
    description: str = field(validator=validators.instance_of(str))
