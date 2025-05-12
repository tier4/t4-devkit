from __future__ import annotations

from enum import Enum

import numpy as np
from attrs import define, field

from .algorithm import GreedyMatcher, MatchingAlgorithmLike
from .policy import AllowAnyPolicy, AllowUnknownPolicy, MatchingPolicyLike, StrictPolicy
from .scorer import CenterDistance, Iou2D, Iou3D, MatchingScorerLike, PlaneDistance

__all__ = [
    "build_matcher",
    "build_matching_scorer",
    "build_matching_policy",
    "MatchingScorer",
    "MatchingPolicy",
    "MatchingAlgorithm",
    "MatchingParams",
]

# ===== Builder Functions =====


def build_matcher(params: MatchingParams) -> MatchingAlgorithmLike:
    """Build a matching algorithm from the parameter.

    Examples:
        >>> params = MatchingParams(...)
        >>> matcher = build_matcher(params)
    """
    scorer = build_matching_scorer(params)
    policy = build_matching_policy(params)
    if params.algorithm == MatchingAlgorithm.GREEDY:
        return GreedyMatcher(
            scorer=scorer,
            policy=policy,
            matchable_threshold=params.matchable_distance,
        )
    else:
        raise ValueError(f"Unexpected algorithm name: {params.algorithm}")


def build_matching_scorer(params: MatchingParams) -> MatchingScorerLike:
    """Build a matching scorer from the parameter.

    Examples:
        >>> params = MatchingParams(...)
        >>> scorer = build_matching_scorer(params)
    """
    if params.scorer == MatchingScorer.CENTER_DISTANCE:
        return CenterDistance()
    elif params.scorer == MatchingScorer.PLANE_DISTANCE:
        return PlaneDistance()
    elif params.scorer == MatchingScorer.IOU2D:
        return Iou2D()
    elif params.scorer == MatchingScorer.IOU3D:
        return Iou3D()
    else:
        raise ValueError(f"Unexpected scorer name: {params.scorer}")


def build_matching_policy(params: MatchingParams) -> MatchingPolicyLike:
    """Build a matching policy from the parameter.

    Examples:
        >>> params = MatchingParams(...)
        >>> policy = build_matching_policy(params)
    """
    if params.policy == MatchingPolicy.STRICT:
        return StrictPolicy()
    elif params.policy == MatchingPolicy.ALLOW_UNKNOWN:
        return AllowUnknownPolicy()
    elif params.policy == MatchingPolicy.ALLOW_ANY:
        return AllowAnyPolicy()
    else:
        raise ValueError(f"Unexpected policy name: {params.policy}")


# ===== Parameters =====


class MatchingScorer(str, Enum):
    """An enum to represent matching scorer names."""

    CENTER_DISTANCE = "CENTER_DISTANCE"
    PLANE_DISTANCE = "PLANE_DISTANCE"
    IOU2D = "IOU2D"
    IOU3D = "IOU3D"
    HEADING_YAW = "HEADING_YAW"


class MatchingPolicy(str, Enum):
    """An enum to represent matching policy names."""

    STRICT = "STRICT"
    ALLOW_UNKNOWN = "ALLOW_UNKNOWN"
    ALLOW_ANY = "ALLOW_ANY"


class MatchingAlgorithm(str, Enum):
    """An enum to represent matching algorithm names."""

    GREEDY = "GREEDY"


@define
class MatchingParams:
    """A dataclass to represent matching parameters.

    Attributes:
        scorer (MatchingScorer): Name of matching scorer.
        policy (MatchingPolicy): Name of matching policy.
        algorithm (MatchingAlgorithm): Name of matching algorithm.
        matchable_distance (float): Max distance from a GT which a estimation can be matched.
    """

    scorer: MatchingScorer = field(default=MatchingScorer.CENTER_DISTANCE, converter=MatchingScorer)
    policy: MatchingPolicy = field(default=MatchingPolicy.STRICT, converter=MatchingPolicy)
    algorithm: MatchingAlgorithm = field(
        default=MatchingAlgorithm.GREEDY,
        converter=MatchingAlgorithm,
    )
    matchable_distance: float = field(default=np.inf)
