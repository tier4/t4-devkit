from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field

if TYPE_CHECKING:
    from t4_devkit.typing import RoiType

__all__ = ["Roi"]


@define
class Roi:
    """A dataclass to represent 2D box ROI.

    Attributes:
        roi (RoiType): Box ROI in the order of (xmin, ymin, xmax, ymax).
    """

    roi: RoiType = field(converter=tuple)

    @roi.validator
    def _check_roi(self, attribute, value) -> None:
        if len(value) != 4:
            raise ValueError(
                f"Expected {attribute.name} is (xmin, ymin, xmax, ymax), but got length with {value}."
            )

        xmin, ymin, xmax, ymax = value
        if (xmax < xmin) or (ymax < ymin):
            raise ValueError(
                f"Expected {attribute.name} is the order of (xmin, ymin, xmax, ymax) and "
                f"xmin <= xmax and ymin <= ymax, but got {value}"
            )

    @property
    def offset(self) -> tuple[int, int]:
        """Return the xy offset from the image origin at the top left of the box.

        Returns:
            Top left corner (x, y).
        """
        return self.roi[:2]

    @property
    def size(self) -> tuple[int, int]:
        """Return the size of the box.

        Returns:
            Box size (width, height).
        """
        return self.roi[2] - self.roi[0], self.roi[3] - self.roi[1]

    @property
    def width(self) -> int:
        """Return the width of the box.

        Returns:
            Box width.
        """
        return self.size[0]

    @property
    def height(self) -> int:
        """Return the height of the box.

        Returns:
            Box height.
        """
        return self.size[1]

    @property
    def center(self) -> tuple[int, int]:
        """Return the center position of the box from the image origin.

        Returns:
            Center position of the box (cx, cy).
        """
        ox, oy = self.offset
        w, h = self.size
        return ox + w // 2, oy + h // 2

    @property
    def area(self) -> int:
        """Return the area of the box.

        Returns:
            Area of the box.
        """
        w, h = self.size
        return w * h
