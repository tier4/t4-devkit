from __future__ import annotations

import numpy as np
from pyquaternion import Quaternion

from t4_devkit.dataclass import LidarPointCloud
from t4_devkit.schema import CalibratedSensor, EgoPose, Sensor
from t4_devkit.viewer import format_entity


def test_format_entity() -> None:
    """Test `format_entity(...)` function."""
    assert "map" == format_entity("map")
    assert "map/base_link" == format_entity("map", "base_link")
    assert "map/base_link" == format_entity("map", "map/base_link")
    assert "map/base_link/camera" == format_entity("map", "map/base_link", "camera")


def test_render_box3ds(dummy_viewer, dummy_box3ds) -> None:
    """Test rendering 3D boxes with `Tier4Viewer`.

    Args:
        dummy_viewer (Tier4Viewer): Viewer object.
        dummy_box3ds (list[Box3D]): List of 3D boxes.
    """
    seconds = 1.0  # [sec]

    dummy_viewer.render_box3ds(seconds, dummy_box3ds)

    centers = [box.position for box in dummy_box3ds]
    rotations = [box.rotation for box in dummy_box3ds]
    sizes = [box.size for box in dummy_box3ds]
    class_ids = [dummy_viewer.label2id[box.semantic_label.name] for box in dummy_box3ds]
    velocities = [box.velocity for box in dummy_box3ds]
    uuids = [box.uuid for box in dummy_box3ds]

    dummy_viewer.render_box3ds(
        seconds,
        centers=centers,
        rotations=rotations,
        sizes=sizes,
        class_ids=class_ids,
        velocities=velocities,
        uuids=uuids,
    )


def test_render_box2ds(dummy_viewer, dummy_box2ds) -> None:
    """Test rendering 2D boxes with `Tier4Viewer`.

    Args:
        dummy_viewer (Tier4Viewer): Viewer object.
        dummy_box2ds (list[Box2D): List of 2D boxes.
    """
    seconds = 1.0  # [sec]

    dummy_viewer.render_box2ds(seconds, dummy_box2ds)

    camera = "camera"
    rois = [box.roi.roi for box in dummy_box2ds]
    class_ids = [dummy_viewer.label2id[box.semantic_label.name] for box in dummy_box2ds]
    uuids = [box.uuid for box in dummy_box2ds]

    dummy_viewer.render_box2ds(seconds, camera=camera, rois=rois, class_ids=class_ids, uuids=uuids)


def test_render_pointcloud(dummy_viewer) -> None:
    """Test rendering pointcloud with `Tier4Viewer`.

    Args:
        dummy_viewer (Tier4Viewer): Viewer object.
    """
    seconds = 1.0  # [sec]

    dummy_pointcloud = LidarPointCloud(np.random.rand(4, 100))
    dummy_viewer.render_pointcloud(seconds, "lidar", dummy_pointcloud)


def test_render_ego(dummy_viewer) -> None:
    """Test rendering ego pose with `Tier4Viewer`.

    Args:
        dummy_viewer (Tier4Viewer): Viewer object.
    """
    seconds = 1.0  # [sec]

    # without `EgoPose`
    translation = [1, 0, 0]
    rotation = Quaternion([0, 0, 0, 1])
    dummy_viewer.render_ego(seconds, translation=translation, rotation=rotation)

    # with `EgoPose`
    ego_pose = EgoPose(
        token="ego",
        translation=translation,
        rotation=rotation,
        timestamp=1e6,
    )
    dummy_viewer.render_ego(ego_pose)


def test_render_calibration(dummy_viewer) -> None:
    """Test rendering sensor calibration with `Tier4Viewer`.

    Args:
        dummy_viewer (Tier4Viewer): Viewer object.
    """
    # without `Sensor` and `CalibratedSensor`
    channel = "camera"
    modality = "camera"
    translation = [1, 0, 0]
    rotation = Quaternion([0, 0, 0, 1])
    camera_intrinsic = [
        [1000.0, 0.0, 100.0],
        [0.0, 1000.0, 100.0],
        [0.0, 0.0, 1.0],
    ]
    dummy_viewer.render_calibration(
        channel=channel,
        modality=modality,
        translation=translation,
        rotation=rotation,
        camera_intrinsic=camera_intrinsic,
    )

    # with `Sensor` and `CalibratedSensor`
    sensor = Sensor(token="sensor", channel="camera", modality="camera")
    calibration = CalibratedSensor(
        token="sensor_calibration",
        sensor_token="sensor",
        translation=translation,
        rotation=rotation,
        camera_intrinsic=camera_intrinsic,
        camera_distortion=[0, 0, 0, 0, 0],
    )
    dummy_viewer.render_calibration(sensor, calibration)
