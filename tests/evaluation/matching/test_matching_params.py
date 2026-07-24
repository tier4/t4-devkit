from __future__ import annotations

import pytest

from t4_devkit.evaluation import MatchingAlgorithm, MatchingParams, MatchingPolicy, MatchingScorer


def test_matching_params_with_objects() -> None:
    _ = MatchingParams(
        scorer=MatchingScorer.CENTER_DISTANCE,
        policy=MatchingPolicy.STRICT,
        algorithm=MatchingAlgorithm.GREEDY,
    )


def test_matching_param_with_str() -> None:
    _ = MatchingParams(scorer="CENTER_DISTANCE", policy="STRICT", algorithm="GREEDY")


def test_matching_param_with_lower_str() -> None:
    """Lower case is not supported to initialize matching params."""

    with pytest.raises(ValueError):
        _ = MatchingParams(scorer="center_distance", policy="strict", algorithm="greedy")
