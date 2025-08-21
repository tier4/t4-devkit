from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.typing import ScalarLike

__all__ = ("us2sec", "sec2us")


def us2sec(timestamp: ScalarLike) -> float:
    """Convert timestamp from micro seconds [us] to seconds [s].

    Args:
        timestamp (ScalarLike): Timestamp in [us].

    Returns:
        Timestamp in [s].
    """
    return 1e-6 * timestamp


def sec2us(timestamp: ScalarLike) -> float:
    """Convert timestamp from seconds [s] to micro seconds [us].

    Args:
        timestamp (ScalarLike): Timestamp in [s].

    Returns:
        Timestamp in [us].
    """
    return 1e6 * timestamp
