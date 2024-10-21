from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from t4_devkit import Tier4
from t4_devkit.dataclass import HomogeneousMatrix, TransformBuffer

from .ground_truth import FrameGroundTruth, SceneGroundTruth

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D
    from t4_devkit.schema import EgoPose, Sample, SampleData

__all__ = ["load_dataset"]


def load_dataset(
    filepath: str,
    frame_id: str | Sequence[str],
    *,
    verbose: bool = False,
) -> SceneGroundTruth:
    """Load ground truths of the specified dataset file.

    Args:
        filepath (str): Path of T4 dataset.
        frame_id (str | Sequence[str]): Box frame ID(s).
        verbose (bool, optional): Whether to display loading dataset.

    Returns:
        Loaded `SceneGroundTruth` object.
    """

    frame_ids = [frame_id] if isinstance(frame_id, str) else frame_id

    t4 = Tier4("annotation", filepath, verbose=verbose)

    frames = [_load_frame_ground_truth(t4, sample, frame_ids) for sample in t4.sample]

    # parse sensor calibrations for each frame id
    sensors = {sensor.channel: sensor for sensor in t4.sensor if sensor.channel in frame_ids}

    return SceneGroundTruth(filepath, frames, sensors)


def _load_frame_ground_truth(
    t4: Tier4,
    sample: Sample,
    frame_ids: Sequence[str],
) -> FrameGroundTruth:
    """Load `FrameGroundTruth` object.

    Args:
        t4 (Tier4): `Tier4` object.
        sample (Sample): Sample record at the current timestamp.
        frame_ids (Sequence[str]): Sequence of frame IDs.

    Returns:
        Loaded `FrameGroundTruth` object.
    """
    sample_data_tokens: dict[str, str] = {}  # frame_id: sample_data_token
    ego_pose_tokens: dict[str, str] = {}  # frame_id: ego_pose_token

    unix_time = sample.timestamp

    for _, sd_token in sample.data.items():
        sample_data: SampleData = t4.get("sample_data", sd_token)
        # TODO: convert lidar or radar modality to base_link or map
        fid = sample_data.channel
        if fid in frame_ids:
            sample_data_tokens[fid] = sd_token

        ego_pose_tokens[sample_data.channel] = sample_data.ego_pose_token

    tf_buffer = _load_tf_buffer(t4, ego_pose_tokens)

    is_3d = True  # TODO

    return (
        _load_ground_truth_3d(t4, unix_time, sample_data_tokens, tf_buffer)
        if is_3d
        else _load_ground_truth_2d(t4, unix_time, sample_data_tokens, tf_buffer)
    )


def _load_ground_truth_3d(
    t4: Tier4,
    unix_time: int,
    sample_data_tokens: dict[str, str],
    tf_buffer: TransformBuffer,
) -> FrameGroundTruth:
    """Load `FrameGroundTruth` object with 3D boxes.

    Args:
        t4 (Tier4): `Tier4` object.
        unix_time (int): Unix timestamp.
        sample_data_tokens (dict[str, str]):
        tf_buffer (TransformBuffer): Transformation buffer.

    Returns:
        Loaded `FrameGroundTruth` object.
    """
    boxes: list[Box3D] = []
    for _, sd_token in sample_data_tokens.items():
        boxes.extend(t4.get_box3ds(sd_token))
    return FrameGroundTruth(unix_time, boxes, tf_buffer)


def _load_ground_truth_2d(
    t4: Tier4,
    unix_time: int,
    sample_data_tokens: dict[str, str],
    tf_buffer: TransformBuffer,
) -> FrameGroundTruth:
    """Load `FrameGroundTruth` object with 2D boxes.

    Args:
        t4 (Tier4): `Tier4` object.
        unix_time (int): Unix timestamp.
        sample_data_tokens (dict[str, str]):
        tf_buffer (TransformBuffer): Transformation buffer.

    Returns:
        Loaded `FrameGroundTruth` object.
    """
    boxes: list[Box2D] = []
    for _, sd_token in sample_data_tokens.items():
        boxes.extend(t4.get_box2ds(sd_token))
    return FrameGroundTruth(unix_time, boxes, tf_buffer)


def _load_tf_buffer(t4: Tier4, ego_pose_tokens: dict[str, str]) -> TransformBuffer:
    """Load transformation buffer.

    Args:
        t4 (Tier4): `Tier4` object.
        ego_pose_tokens (dict[str, str]):

    Returns:
        Loaded `TransformBuffer` object.
    """
    tf_buffer = TransformBuffer()

    for _, ego_token in ego_pose_tokens.items():
        ego_pose: EgoPose = t4.get("ego_pose", ego_token)

        tf_matrix = HomogeneousMatrix(
            ego_pose.translation,
            ego_pose.rotation,
            src="map",
            dst="base_link",
        )

        tf_buffer.set_transform(tf_matrix)

    return tf_buffer
