from __future__ import annotations

from numpy.typing import ArrayLike

__all__ = ["RoiLike"]


class RoiLike(tuple):
    """A 4-element tuple representing a region of interest (ROI).

    This class ensures that the array always has the correct shape and value order.
    It can be constructed from any array-like object that can be converted to a tuple of length 4.

    Examples:
        >>> roi = RoiLike((10, 20, 30, 40)) # OK
        >>> roi = RoiLike([10, 20, 30, 40]) # OK
        >>> roi = RoiLike([10, 20])         # ValueError: ROI must be 4-elements
        >>> roi = RoiLike([40, 30, 20, 10]) # ValueError: ROI must be xmin <= xmax && ymin <= ymax
    """

    def __new__(cls, input_array: ArrayLike) -> RoiLike:
        """Create a new RoiLike instance.

        Args:
            input_array (ArrayLike): An array-like object that can be converted to a tuple of length 4.

        Returns:
            RoiLike instance.

        Raises:
            ValueError: If the input array is not a 4-element tuple
                or if the values are not in the correct order.
        """
        if not isinstance(input_array, tuple):
            input_array = tuple(input_array)

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
