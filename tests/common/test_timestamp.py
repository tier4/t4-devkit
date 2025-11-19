from __future__ import annotations

from t4_devkit.common.timestamp import microseconds2seconds, seconds2microseconds


def test_timestamp() -> None:
    """Test timestamp conversion."""
    seconds = 1e-6

    us = seconds2microseconds(seconds)
    sec = microseconds2seconds(us)

    assert us == 1
    assert sec == 1e-6
