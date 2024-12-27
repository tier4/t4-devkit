from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
from pyquaternion import Quaternion

from t4_devkit.dataclass import (
    Box2D,
    Box3D,
    HomogeneousMatrix,
    SemanticLabel,
    Shape,
    ShapeType,
    Trajectory,
    TransformBuffer,
)

if TYPE_CHECKING:
    from t4_devkit.typing import NDArrayFloat


@pytest.fixture(scope="module")
def label2id() -> dict[str, int]:
    return {"car": 0, "bicycle": 1, "pedestrian": 2}


@pytest.fixture(scope="function")
def dummy_box3d() -> Box3D:
    """Return a dummy 3D box.

    Returns:
        A 3D box.
    """
    return Box3D(
        unix_time=100,
        frame_id="base_link",
        semantic_label=SemanticLabel("car"),
        position=(1.0, 1.0, 1.0),
        rotation=Quaternion([1.0, 0.0, 0.0, 0.0]),
        shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
        velocity=(1.0, 1.0, 1.0),
        confidence=1.0,
        uuid="car3d_0",
    )


@pytest.fixture(scope="function")
def dummy_box3ds() -> list[Box3D]:
    """Return a list of dummy 3D boxes.

    Returns:
        List of 3D boxes.
    """
    return [
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("car"),
            position=(1.0, 1.0, 1.0),
            rotation=Quaternion([1.0, 0.0, 0.0, 0.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="car3d_1",
        ),
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("bicycle"),
            position=(-1.0, -1.0, 1.0),
            rotation=Quaternion([1.0, 0.0, 0.0, 0.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="bicycle3d_1",
        ),
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("pedestrian"),
            position=(-1.0, 1.0, 1.0),
            rotation=Quaternion([1.0, 0.0, 0.0, 0.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="pedestrian3d_1",
        ),
    ]


@pytest.fixture(scope="function")
def dummy_box2d() -> Box2D:
    """Return a dummy 2D box.

    Returns:
        A 2D box.
    """
    return Box2D(
        unix_time=100,
        frame_id="camera",
        semantic_label=SemanticLabel("car"),
        roi=(100, 100, 150, 150),
        confidence=1.0,
        uuid="car2d_0",
    )


@pytest.fixture(scope="function")
def dummy_box2ds() -> list[Box2D]:
    """Return a list of dummy 2D boxes.

    Returns:
        List of 2D boxes.
    """
    return [
        Box2D(
            unix_time=100,
            frame_id="camera",
            semantic_label=SemanticLabel("car"),
            roi=(100, 100, 150, 150),
            confidence=1.0,
            uuid="car2d_1",
        ),
        Box2D(
            unix_time=100,
            frame_id="camera",
            semantic_label=SemanticLabel("bicycle"),
            roi=(50, 50, 60, 60),
            confidence=1.0,
            uuid="bicycle2d_1",
        ),
        Box2D(
            unix_time=100,
            frame_id="camera",
            semantic_label=SemanticLabel("pedestrian"),
            roi=(150, 150, 170, 170),
            confidence=1.0,
            uuid="pedestrian2d_1",
        ),
    ]


@pytest.fixture(scope="function")
def dummy_trajectory() -> Trajectory:
    """Return a dummy trajectory.

    Returns:
        A trajectory.
    """
    # list item is converted to NDArray internally
    return Trajectory(
        waypoints=[[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]],
        confidence=1.0,
    )


@pytest.fixture(scope="module")
def dummy_tf_buffer() -> TransformBuffer:
    """Return a dummy transformation buffer.

    Returns:
        Buffer includes `base_link` to `map` and `base_link` to `camera` transformation.
    """
    tf_buffer = TransformBuffer()

    tf_buffer.set_transform(
        HomogeneousMatrix(
            [1.0, 1.0, 1.0],
            Quaternion([1.0, 0.0, 0.0, 0.0]),
            src="base_link",
            dst="map",
        )
    )

    tf_buffer.set_transform(
        HomogeneousMatrix(
            [1.0, 1.0, 1.0],
            Quaternion([1.0, 0.0, 0.0, 0.0]),
            src="base_link",
            dst="camera",
        )
    )

    return tf_buffer


@pytest.fixture(scope="function")
def dummy_camera_calibration() -> tuple[tuple[int, int], NDArrayFloat]:
    img_size = (1280, 720)

    intrinsic = np.array(
        [
            [1000, 0, 640],
            [0, 1000, 360],
            [0, 0, 1],
        ]
    )

    return img_size, intrinsic
