import pytest
from pyquaternion import Quaternion

from t4_devkit.dataclass import Box2D, Box3D, LabelID, SemanticLabel, Shape, ShapeType


@pytest.fixture(scope="module")
def dummy_box3d() -> Box3D:
    """Return a dummy 3D box.

    Returns:
        A 3D box.
    """
    return Box3D(
        unix_time=100,
        frame_id="base_link",
        semantic_label=SemanticLabel(label=LabelID.CAR, original="car"),
        position=(1.0, 1.0, 1.0),
        rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
        shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
        velocity=(1.0, 1.0, 1.0),
        confidence=1.0,
        uuid="car3d_0",
    )


@pytest.fixture(scope="module")
def dummy_box3ds() -> list[Box3D]:
    """Return a list of dummy 3D boxes.

    Returns:
        List of 3D boxes.
    """
    return [
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel(label=LabelID.CAR, original="car"),
            position=(1.0, 1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="car3d_1",
        ),
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel(label=LabelID.BICYCLE, original="bicycle"),
            position=(-1.0, -1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="bicycle3d_1",
        ),
        Box3D(
            unix_time=100,
            frame_id="base_link",
            semantic_label=SemanticLabel(label=LabelID.PEDESTRIAN, original="pedestrian"),
            position=(-1.0, 1.0, 1.0),
            rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
            velocity=(1.0, 1.0, 1.0),
            confidence=1.0,
            uuid="pedestrian3d_1",
        ),
    ]


@pytest.fixture(scope="module")
def dummy_box2d() -> Box2D:
    """Return a dummy 2D box.

    Returns:
        A 2D box.
    """
    return Box2D(
        unix_time=100,
        frame_id="camera",
        semantic_label=SemanticLabel(label=LabelID.CAR, original="car"),
        roi=(100, 100, 50, 50),
        confidence=1.0,
        uuid="car2d_0",
    )


@pytest.fixture(scope="module")
def dummy_box2ds() -> list[Box2D]:
    """Return a list of dummy 2D boxes.

    Returns:
        List of 2D boxes.
    """
    return [
        Box2D(
            unix_time=100,
            frame_id="camera",
            semantic_label=SemanticLabel(label=LabelID.CAR, original="car"),
            roi=(100, 100, 50, 50),
            confidence=1.0,
            uuid="car2d_1",
        ),
        Box2D(
            unix_time=100,
            frame_id="camera",
            semantic_label=SemanticLabel(label=LabelID.BICYCLE, original="bicycle"),
            roi=(50, 50, 10, 10),
            confidence=1.0,
            uuid="bicycle2d_1",
        ),
        Box2D(
            unix_time=100,
            frame_id="camera",
            semantic_label=SemanticLabel(label=LabelID.PEDESTRIAN, original="pedestrian"),
            roi=(150, 150, 20, 20),
            confidence=1.0,
            uuid="pedestrian2d_1",
        ),
    ]