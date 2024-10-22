from __future__ import annotations

from t4_devkit.evaluation import BoxMatch, FrameBoxMatch, MatchingParams, build_matcher

# TODO(ktro2828): Fix following tests!!


def test_box_match(dummy_evaluation_box3ds) -> None:
    estimations, ground_truths = dummy_evaluation_box3ds

    matcher = build_matcher(params=MatchingParams())

    matches = matcher(estimations, ground_truths)

    assert isinstance(matches, list)
    assert all(isinstance(m, BoxMatch) for m in matches)


def test_frame_box_match(dummy_evaluation_box3ds) -> None:
    estimations, ground_truths = dummy_evaluation_box3ds

    matcher = build_matcher(params=MatchingParams())

    matches = matcher(estimations, ground_truths)

    _ = FrameBoxMatch(unix_time=100, frame_index=0, matches=matches)
