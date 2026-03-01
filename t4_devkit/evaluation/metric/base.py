from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.evaluation import FrameBoxMatch, FrameSegmentation


class BaseMetric(ABC):
    @abstractmethod
    def __call__(self, frames: list[FrameBoxMatch | FrameSegmentation]) -> float:
        """Compute metric score."""
        ...
