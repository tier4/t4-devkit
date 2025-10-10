from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .result import GroupName, Report, TargetName

if TYPE_CHECKING:
    pass


class Checker(ABC):
    group: GroupName
    target: TargetName

    @abstractmethod
    def __call__(self, *args, **kwargs) -> list[Report]:
        pass


class SchemaFormatChecker(Checker):
    def __call__(self, data_root: str) -> list[Report]:
        pass
