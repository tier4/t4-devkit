from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define
from typing_extensions import deprecated

if TYPE_CHECKING:
    from t4_devkit.typing import ScalarLike


__all__ = ["microseconds2seconds", "seconds2microseconds", "Stamp"]


@deprecated("Please use `microseconds2seconds(...)` instead.")
def us2sec(timestamp: ScalarLike) -> float:
    """Convert timestamp from micro seconds [us] to seconds [s].

    Deprecated:
        This function is deprecated. Please use `microseconds2seconds(...)` instead.

    Args:
        timestamp (ScalarLike): Timestamp in [us].

    Returns:
        Timestamp in [s].
    """
    return microseconds2seconds(timestamp)


@deprecated("Please use `seconds2microseconds(...)` instead.")
def sec2us(timestamp: ScalarLike) -> float:
    """Convert timestamp from seconds [s] to micro seconds [us].

    Deprecated:
        This function is deprecated. Please use `seconds2microseconds(...)` instead.

    Args:
        timestamp (ScalarLike): Timestamp in [s].

    Returns:
        Timestamp in [us].
    """
    return seconds2microseconds(timestamp)


def microseconds2seconds(timestamp: ScalarLike) -> float:
    """Convert timestamp from micro seconds [us] to seconds [s].

    Args:
        timestamp (ScalarLike): Timestamp in [us].

    Returns:
        Timestamp in [s].
    """
    return 1e-6 * timestamp


def seconds2microseconds(timestamp: ScalarLike) -> float:
    """Convert timestamp from seconds [s] to micro seconds [us].

    Args:
        timestamp (ScalarLike): Timestamp in [s].

    Returns:
        Timestamp in [us].
    """
    return 1e6 * timestamp


@define
class Stamp:
    """A dataclass to represent timestamp.

    Attributes:
        sec (int): Seconds.
        nanosec (int): Nanoseconds.
    """

    sec: int
    nanosec: int

    @property
    def in_seconds(self) -> float:
        """Convert timestamp to seconds as a float.

        Returns:
            float: Timestamp in seconds.
        """
        return self.sec + self.nanosec * 1e-9
