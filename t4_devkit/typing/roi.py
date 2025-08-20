from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from t4_devkit.typing import ScalarLike

__all__ = ["Roi"]


class Roi(tuple):
    """A 4-element tuple representing a region of interest (ROI).

    This class ensures that the array always has the correct shape and value order.
    It can be constructed from any array-like object that can be converted to a tuple of length 4,
    or from individual numeric arguments.

    Examples:
        >>> roi = Roi(10, 20, 30, 40)   # OK
        >>> roi = Roi((10, 20, 30, 40)) # OK
        >>> roi = Roi([10, 20, 30, 40]) # OK
        >>> roi = Roi([10, 20])         # ValueError: ROI must be 4-elements
        >>> roi = Roi([40, 30, 20, 10]) # ValueError: ROI must be xmin <= xmax && ymin <= ymax
    """

    def __new__(cls, *args: Any) -> Roi:
        """Create a new Roi instance.

        Args:
            *args: Either a single array-like object with 4 elements, or 4 individual numeric values.

        Returns:
            Roi instance.

        Raises:
            ValueError: If the input is not 4 elements or if the values are not in the correct order.
        """
        # Handle different input formats
        if len(args) == 1:
            # Single argument - should be an iterable
            try:
                input_array = tuple(args[0])
            except TypeError:
                # Not iterable, treat as single value
                input_array = args
        elif len(args) == 4:
            # Four individual arguments
            input_array = args
        else:
            # Wrong number of arguments
            input_array = args

        # validate input shape of the array
        if len(input_array) != 4:
            raise ValueError(f"ROI must be a 4-element tuple: {input_array}")

        # validate input value order of the array
        xmin, ymin, xmax, ymax = input_array
        if xmax < xmin or ymax < ymin:
            raise ValueError(
                f"ROI must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: {input_array}"
            )

        return super().__new__(cls, input_array)

    @property
    def offset(self) -> tuple[ScalarLike, ScalarLike]:
        """Return the xy offset from the image origin at the top left corner."""
        xmin, ymin, *_ = self
        return xmin, ymin

    @property
    def size(self) -> tuple[ScalarLike, ScalarLike]:
        """Return the width and height of the ROI."""
        xmin, ymin, xmax, ymax = self
        return xmax - xmin, ymax - ymin

    @property
    def width(self) -> ScalarLike:
        """Return the width of the ROI."""
        return self.size[0]

    @property
    def height(self) -> ScalarLike:
        """Return the height of the ROI."""
        return self.size[1]

    @property
    def center(self) -> tuple[ScalarLike, ScalarLike]:
        """Return the center position of the ROI."""
        xmin, ymin, xmax, ymax = self
        return (xmin + xmax) / 2, (ymin + ymax) / 2

    @property
    def area(self) -> ScalarLike:
        """Return the area of the ROI."""
        return self.width * self.height
