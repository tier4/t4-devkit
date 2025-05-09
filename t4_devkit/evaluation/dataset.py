from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define

from t4_devkit import Tier4

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxLike


__all__ = ["load_dataset", "FrameGroundTruth", "SceneGroundTruth"]


def load_dataset(data_root: str) -> SceneGroundTruth:
    """Load dataset.

    Args:
        data_root (str): Root directory path to the dataset.

    Returns:
        SceneGroundTruth: Loaded container of ground truths.
    """
    t4 = Tier4("annotation", data_root=data_root, verbose=False)

    frames: list[FrameGroundTruth] = []
    for i, sample in enumerate(t4.sample):
        boxes = list(map(t4.get_box3d, sample.ann_3ds))
        frames.append(FrameGroundTruth(unix_time=sample.timestamp, frame_index=i, boxes=boxes))

    return SceneGroundTruth(data_root=data_root, frames=frames)


@define
class FrameGroundTruth:
    """A container of boxes at a single frame.

    Attributes:
        unix_time (int): Unix timestamp.
        frame_index (int): Index number of the frame.
        boxes (list[BoxLike]): List of ground truth instances.
    """

    unix_time: int
    frame_index: int
    boxes: list[BoxLike]


@define
class SceneGroundTruth:
    """A container of frame ground truths.

    Attributes:
        data_root (str): Root directory path to the dataset.
        frames (list[FrameGroundTruth]): List of frame ground truths.
    """

    data_root: str
    frames: list[FrameGroundTruth]

    def lookup_frame(self, unix_time: int, tolerance: int) -> FrameGroundTruth | None:
        """Lookup the closest set of ground truth frame.

        Return None if the minimum time difference exceeds `tolerance`.

        Args:
            unix_time (int): Unix timestamp.
            tolerance (int): Time difference tolerance in micro seconds.

        Returns:
            Return frame ground truth if succeeded, otherwise None.
        """
        closest = min(self.frames, key=lambda f: abs(unix_time - f.unix_time))
        return closest if abs(unix_time - closest.unix_time) <= tolerance else None
