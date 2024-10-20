from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.typing import RoiType

__all__ = ["Roi"]


@dataclass
class Roi:
    roi: RoiType

    def __post_init__(self) -> None:
        assert len(self.roi) == 4, (
            "Expected roi is (x, y, width, height), " f"but got length with {len(self.roi)}."
        )

        if not isinstance(self.roi, tuple):
            self.roi = tuple(self.roi)

    @property
    def offset(self) -> tuple[int, int]:
        return self.roi[:2]

    @property
    def size(self) -> tuple[int, int]:
        return self.roi[2:]

    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]

    @property
    def center(self) -> tuple[int, int]:
        ox, oy = self.offset
        w, h = self.size
        return ox + w // 2, oy + h // 2

    @property
    def area(self) -> int:
        w, h = self.size
        return w * h
