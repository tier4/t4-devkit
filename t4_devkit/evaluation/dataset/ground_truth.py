from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType, TransformBuffer
    from t4_devkit.schema import CalibratedSensor


@dataclass(frozen=True)
class SceneGroundTruth:
    """A dataclass to store a set of ground truths and static sensor data.

    Attributes:
        filepath (str): Root path of the dataset.
        frames (list[FrameGroundTruth]): List of a set of ground truths at each frame.
        sensors (dict[str, CalibratedSensor]): A set of
    """

    filepath: str
    frames: list[FrameGroundTruth]
    sensors: dict[str, CalibratedSensor]

    def find_nearest(self, unix_time: int, threshold: int) -> FrameGroundTruth | None:
        """Find a `FrameGround` object at the nearest time of the specified timestamp.

        If it could be found, returns `None`.

        Args:
            unix_time (int): Unix time to search.
            threshold (int): Threshold value of the time difference.

        Returns:
            Return `None`, if it could not find any corresponding ground truth.
        """
        min_diff_time = float("inf")
        output: FrameGroundTruth | None = None

        for frame in self.frames:
            diff_time = abs(unix_time - frame.unix_time)
            if diff_time < threshold and diff_time < min_diff_time:
                min_diff_time = diff_time
                output = frame

        return output


@dataclass(frozen=True)
class FrameGroundTruth:
    """A dataclass to represent a set of ground truths at a single frame."""

    unix_time: int
    boxes: list[BoxType]
    tf_buffer: TransformBuffer
