from __future__ import annotations

import numpy as np
from pyquaternion import Quaternion

from t4_devkit.dataclass import LidarPointCloud
from t4_devkit.schema import CalibratedSensor, EgoPose, Sensor
from t4_devkit.viewer import Tier4Viewer


def test_tier4_viewer(dummy_box3ds, dummy_box2ds) -> None:
    """Test `Tier4Viewer` class.

    Args:
        dummy_box3ds (list[Box3D]): List of `Box3D`s.
        dummy_box2ds (list[Box2D]): List of `Box2D`s.
    """
    viewer = Tier4Viewer("test_viewer", cameras=["camera"], spawn=False)

    seconds = 1.0  # [sec]

    # test render_box3ds(...)
    viewer.render_box3ds(seconds, dummy_box3ds)

    # test render_box2ds(...)
    viewer.render_box2ds(seconds, dummy_box2ds)

    # test render_pointcloud(...)
    dummy_pointcloud = LidarPointCloud(np.random.rand(4, 100))
    viewer.render_pointcloud(seconds, "lidar", dummy_pointcloud)

    # test render_ego(...)
    # without `EgoPose`
    ego_translation = [1, 0, 0]
    ego_rotation = Quaternion([0, 0, 0, 1])
    viewer.render_ego(seconds, ego_translation, ego_rotation)

    # with `EgoPose`
    ego_pose = EgoPose(
        token="ego",
        translation=ego_translation,
        rotation=ego_rotation,
        timestamp=1e6,
    )
    viewer.render_ego(ego_pose)

    # test render_calibration(...)
    # without `Sensor` and `CalibratedSensor`
    channel = "camera"
    modality = "camera"
    camera_translation = [1, 0, 0]
    camera_rotation = Quaternion([0, 0, 0, 1])
    camera_intrinsic = [
        [1000.0, 0.0, 100.0],
        [0.0, 1000.0, 100.0],
        [0.0, 0.0, 1.0],
    ]
    viewer.render_calibration(
        channel,
        modality,
        camera_translation,
        camera_rotation,
        camera_intrinsic,
    )

    # with `Sensor` and `CalibratedSensor`
    sensor = Sensor(token="sensor", channel="camera", modality="camera")
    calibration = CalibratedSensor(
        token="sensor_calibration",
        sensor_token="sensor",
        translation=camera_translation,
        rotation=camera_rotation,
        camera_intrinsic=camera_intrinsic,
        camera_distortion=[0, 0, 0, 0, 0],
    )
    viewer.render_calibration(sensor, calibration)
