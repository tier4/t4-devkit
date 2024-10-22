from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType

    from .parameter import MatchingParams


class MatchingContext:
    def __init__(self, params: MatchingParams) -> None:
        pass

    def do_matching(self, box1: BoxType, box2: BoxType) -> float | None:
        pass
