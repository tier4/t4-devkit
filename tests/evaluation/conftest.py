from __future__ import annotations

import pytest
from pyquaternion import Quaternion

from t4_devkit.dataclass import Box2D, Box3D, SemanticLabel, Shape, ShapeType


@pytest.fixture(scope="module")
def dummy_evaluation_box3ds() -> tuple[list[Box3D], list[Box3D]]:
    estimations = [
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("car"),
            position=(1.0, 1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="estimation_car3d_1",
        ),
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("bicycle"),
            position=(-1.0, -1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="estimation_bicycle3d_1",
        ),
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("car"),
            position=(-1.0, 1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="estimation_car3d_1",
        ),
    ]

    ground_truths = [
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("car"),
            position=(1.0, 1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            num_points=10,
            confidence=1.0,
            uuid="gt_car3d_1",
        ),
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("bicycle"),
            position=(-1.0, -1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            num_points=10,
            confidence=1.0,
            uuid="gt_bicycle3d_1",
        ),
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel("pedestrian"),
            position=(-1.0, 1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="gt_pedestrian3d_1",
        ),
    ]

    return estimations, ground_truths


@pytest.fixture(scope="module")
def dummy_evaluation_box2ds() -> tuple[list[Box2D], list[Box2D]]:
    pass
