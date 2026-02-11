from __future__ import annotations

import os.path as osp
from typing import TYPE_CHECKING

import numpy as np
from attrs import define

from t4_devkit import Tier4
from t4_devkit.dataclass import BoxLike, HomogeneousMatrix, TransformBuffer
from t4_devkit.typing import NDArray

from .task import EvaluationTask

if TYPE_CHECKING:
    from t4_devkit.schema import EgoPose, ObjectAnn, Sample, SampleData, Sensor, SurfaceAnn

__all__ = ["EvaluationObjectLike", "load_dataset", "FrameGroundTruth", "SceneGroundTruth"]


EvaluationObjectLike = list[BoxLike] | dict[str, NDArray]
"""Type alias for evaluation objects.

Accepts:
    list[BoxLike]: Boxes.
    dict[str, NDArray]: Semantic masks for each camera in the shape of (H, W).
"""


def load_dataset(data_root: str, task: EvaluationTask) -> SceneGroundTruth:
    """Load dataset.

    Args:
        data_root (str): Root directory path to the dataset.
        task (EvaluationTask): Evaluation task.

    Returns:
        SceneGroundTruth: Loaded container of ground truths.
    """
    t4 = Tier4(data_root, verbose=False)

    frames: list[FrameGroundTruth] = []
    for i, sample in enumerate(t4.sample):
        # annotations
        if task.is_segmentation():
            annotations = (
                _load_segmentation2d(t4, sample)
                if task.is_2d()
                else _load_segmentation3d(t4, sample)
            )
        else:
            # TODO(ktro2828): add support of prediction future
            annotations = (
                list(map(t4.get_box3d, sample.ann_3ds))
                if task.is_3d()
                else list(map(t4.get_box2d, sample.ann_2ds))
            )

        if annotations is None:
            continue

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
                annotations=annotations,
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


def _load_segmentation2d(t4: Tier4, sample: Sample) -> dict[str, NDArray]:
    """Load 2D segmentation masks for each channel."""
    masks: dict[str, NDArray] = {}
    for channel, token in sample.data.items():
        sample_data: SampleData = t4.get("sample_data", token)
        masks[channel] = np.zeros((sample_data.height, sample_data.width), dtype=np.uint8)

    for token in sample.ann_2ds:
        object_ann: ObjectAnn = t4.get("object_ann", token)
        sample_data: SampleData = t4.get("sample_data", object_ann.sample_data_token)
        masks[sample_data.channel] += object_ann.mask.decode()

    for token in sample.surface_anns:
        surface_ann: SurfaceAnn = t4.get("surface_ann", token)
        sample_data: SampleData = t4.get("sample_data", surface_ann.sample_data_token)
        masks[sample_data.channel] += surface_ann.mask.decode()

    return masks


def _load_segmentation3d(t4: Tier4, sample: Sample) -> dict[str, NDArray] | None:
    """Load 3D pointcloud labels.

    Args:
        t4 (Tier4): Tier4 instance.
        sample (Sample): Sample record.

    Returns:
        dict[str, NDArray] | None: Return label array in the shape of (N,)
            if the corresponding lidarseg exists, otherwise None.
    """
    channel: str | None = None
    label: NDArray | None = None
    for lidarseg in t4.lidarseg:
        for key, token in sample.data.items():
            if lidarseg.sample_data_token == token:
                channel = key
        if channel is None:
            continue
        filepath = osp.join(t4.data_root, lidarseg.filename)
        label = np.fromfile(filepath, dtype=np.uint8)
    return {channel: label} if channel and label else None


@define
class FrameGroundTruth:
    """A container of boxes at a single frame.

    Attributes:
        unix_time (int): Unix timestamp.
        frame_index (int): Index number of the frame.
        annotations (EvaluationObjectLike): Set of ground truth instances.
        ego2map (HomogeneousMatrix): Transformation matrix from ego to map coordinate.
    """

    unix_time: int
    frame_index: int
    annotations: EvaluationObjectLike
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
