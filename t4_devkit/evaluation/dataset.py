from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define

from t4_devkit import Tier4
from t4_devkit.dataclass import HomogeneousMatrix, TransformBuffer

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxLike
    from t4_devkit.schema import EgoPose, Sensor


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
        # annotation boxes
        boxes = list(map(t4.get_box3d, sample.ann_3ds))

        # transformation matrix from ego to map
        ego_pose = _closest_ego_pose(t4, sample.timestamp)
        ego2map = HomogeneousMatrix(
            position=ego_pose.translation,
            rotation=ego_pose.rotation,
            src="base_link",
            dst="map",
        )

        frames.append(
            FrameGroundTruth(
                unix_time=sample.timestamp,
                frame_index=i,
                boxes=boxes,
                ego2map=ego2map,
            )
        )

    # transformation matrices from ego to each sensor
    ego2sensors = TransformBuffer()
    for cs_record in t4.calibrated_sensor:
        sensor: Sensor = t4.get("sensor", cs_record.sensor_token)
        matrix = HomogeneousMatrix(
            position=cs_record.translation,
            rotation=cs_record.rotation,
            src="base_link",
            dst=sensor.channel,
        )

        ego2sensors.set_transform(matrix)

    return SceneGroundTruth(data_root=data_root, frames=frames, ego2sensors=ego2sensors)


def _closest_ego_pose(t4: Tier4, timestamp: int) -> EgoPose:
    """Lookup the ego pose record at the closest timestamp."""
    return min(t4.ego_pose, key=lambda e: abs(e.timestamp - timestamp))


@define
class FrameGroundTruth:
    """A container of boxes at a single frame.

    Attributes:
        unix_time (int): Unix timestamp.
        frame_index (int): Index number of the frame.
        boxes (list[BoxLike]): List of ground truth instances.
        ego2map (HomogeneousMatrix): Transformation matrix from ego to map coordinate.
    """

    unix_time: int
    frame_index: int
    boxes: list[BoxLike]
    ego2map: HomogeneousMatrix


@define
class SceneGroundTruth:
    """A container of frame ground truths.

    Attributes:
        data_root (str): Root directory path to the dataset.
        frames (list[FrameGroundTruth]): List of frame ground truths.
        ego2sensors (TransformBuffer): Buffer of transformation matrices from ego to each sensor coordinates.
    """

    data_root: str
    frames: list[FrameGroundTruth]
    ego2sensors: TransformBuffer

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
