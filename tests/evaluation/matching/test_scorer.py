from __future__ import annotations

import math

import pytest
from pyquaternion import Quaternion

from t4_devkit.dataclass import Box3D, SemanticLabel, Shape, ShapeType
from t4_devkit.evaluation import CenterDistance, Iou2D, Iou3D, PlaneDistance


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
        semantic_label=SemanticLabel("car"),
        position=(1.0, 1.0, 1.0),
        rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
        shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
        velocity=(1.0, 1.0, 1.0),
        num_points=10,
        confidence=1.0,
        uuid="gt_car3d_1",
    )


def test_center_distance(estimation, ground_truth) -> None:
    scorer = CenterDistance()

    score = scorer(estimation, ground_truth)

    assert math.isclose(score, 0.0)


def test_plane_distance(estimation, ground_truth) -> None:
    scorer = PlaneDistance()

    score = scorer(estimation, ground_truth)

    assert math.isclose(score, 0.0)


def test_iou2d(estimation, ground_truth) -> None:
    scorer = Iou2D()

    score = scorer(estimation, ground_truth)

    assert math.isclose(score, 1.0)


def test_iou3d(estimation, ground_truth) -> None:
    scorer = Iou3D()

    score = scorer(estimation, ground_truth)

    assert math.isclose(score, 1.0)
