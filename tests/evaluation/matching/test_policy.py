from __future__ import annotations

import pytest
from pyquaternion import Quaternion

from t4_devkit.dataclass import Box3D, SemanticLabel, Shape, ShapeType
from t4_devkit.evaluation import AllowAnyPolicy, AllowUnknownPolicy, StrictPolicy


@pytest.fixture(scope="module")
def estimation() -> Box3D:
    return Box3D(
        unix_time=100,
        frame_id="base_link",
        semantic_label=SemanticLabel("car"),
        position=(1.0, 1.0, 1.0),
        rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
        shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
        velocity=(1.0, 1.0, 1.0),
        confidence=1.0,
        uuid="estimation_car3d_1",
    )


@pytest.fixture(scope="module")
def ground_truth() -> Box3D:
    return Box3D(
        unix_time=100,
        frame_id="base_link",
        semantic_label=SemanticLabel("unknown"),
        position=(1.0, 1.0, 1.0),
        rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
        shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
        velocity=(1.0, 1.0, 1.0),
        num_points=10,
        confidence=1.0,
        uuid="gt_car3d_1",
    )


def test_strict_policy(estimation, ground_truth) -> None:
    policy = StrictPolicy()

    assert policy.is_matchable(estimation, ground_truth) is False


def test_allow_unknown_policy(estimation, ground_truth) -> None:
    policy = AllowUnknownPolicy()

    assert policy.is_matchable(estimation, ground_truth)


def test_allow_any_policy(estimation, ground_truth) -> None:
    policy = AllowAnyPolicy()

    assert policy.is_matchable(estimation, ground_truth)
