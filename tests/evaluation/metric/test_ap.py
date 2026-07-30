from __future__ import annotations

import math

import pytest

from t4_devkit.dataclass import HomogeneousMatrix
from t4_devkit.evaluation import (
    Ap,
    ApH,
    CenterDistance,
    FrameBoxMatch,
    MatchingParams,
    build_matcher,
)


@pytest.fixture(scope="module")
def dummy_frame3d(dummy_evaluation_box3ds) -> FrameBoxMatch:
    estimations, ground_truths = dummy_evaluation_box3ds

    matcher = build_matcher(params=MatchingParams())

    matches = matcher(estimations, ground_truths)

    ego2map = HomogeneousMatrix(
        position=(1, 0, 0),
        rotation=(1, 0, 0, 0),
        src="base_link",
        dst="map",
    )

    return FrameBoxMatch(unix_time=100, frame_index=0, matches=matches, ego2map=ego2map)


def test_ap(dummy_frame3d) -> None:
    ap = Ap(scorer=CenterDistance(), threshold=1.0)

    score = ap(frames=[dummy_frame3d])

    assert math.isclose(score, 0.394, rel_tol=1e-3)


def test_aph(dummy_frame3d) -> None:
    aph = ApH(scorer=CenterDistance(), threshold=1.0)

    score = aph(frames=[dummy_frame3d])

    assert math.isclose(score, 0.394, rel_tol=1e-3)
