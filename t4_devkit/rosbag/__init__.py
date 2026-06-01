from __future__ import annotations

try:
    from rosbags.rosbag2 import Reader as _Reader  # noqa: F401
except ImportError as e:
    raise ImportError(
        "rosbags is required for rosbag support. " "Install it with: pip install t4-devkit[rosbag]"
    ) from e

from .reader import Rosbag2Reader

__all__ = ["Rosbag2Reader"]
