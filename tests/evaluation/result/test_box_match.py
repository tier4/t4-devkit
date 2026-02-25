from __future__ import annotations

from t4_devkit.dataclass import HomogeneousMatrix
from t4_devkit.evaluation import (
    BoxMatch,
    FrameBoxMatch,
    MatchingParams,
    build_matcher,
    build_matching_scorer,
)


def test_box_match(dummy_evaluation_box3ds) -> None:
    estimations, ground_truths = dummy_evaluation_box3ds

    matcher = build_matcher(params=MatchingParams())

    matches = matcher(estimations, ground_truths)

    assert isinstance(matches, list)
    assert all(isinstance(m, BoxMatch) for m in matches)
    assert len(matches) == 4


def test_frame_box_match(dummy_evaluation_box3ds) -> None:
    estimations, ground_truths = dummy_evaluation_box3ds

    matcher = build_matcher(params=MatchingParams())

    matches = matcher(estimations, ground_truths)

    ego2map = HomogeneousMatrix(
        position=(1, 0, 0),
        rotation=(1, 0, 0, 0),
        src="base_link",
        dst="map",
    )

    frame = FrameBoxMatch(unix_time=100, frame_index=0, matches=matches, ego2map=ego2map)

    scorer = build_matching_scorer(params=MatchingParams())
    threshold = 1.0

    assert frame.num_estimation == 3
    assert frame.num_gt == 3
    assert frame.num_tp(scorer=scorer, threshold=threshold) == 2
    assert frame.num_fp(scorer=scorer, threshold=threshold) == 1
    assert frame.num_fn(scorer=scorer, threshold=threshold) == 1
    assert frame.num_tn(scorer=scorer, threshold=threshold) == 0
