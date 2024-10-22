from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


class MatchingScorer(str, Enum):
    CENTER_DISTANCE = "CENTER_DISTANCE"
    PLANE_DISTANCE = "PLANE_DISTANCE"
    IOU2D = "IOU2D"
    IOU3D = "IOU3D"


class MatchingPolicy(str, Enum):
    STRICT = "STRICT"
    ALLOW_UNKNOWN = "ALLOW_UNKNOWN"
    ALLOW_ANY = "ALLOW_ANY"


class MatchingAlgorithm(str, Enum):
    GREEDY = "GREEDY"


@dataclass
class MatchingParams:
    scorer: MatchingScorer = MatchingScorer.CENTER_DISTANCE
    policy: MatchingPolicy = MatchingPolicy.STRICT
    algorithm: MatchingAlgorithm = MatchingAlgorithm.GREEDY
    matchable_distance: float = np.inf

    def __post_init__(self) -> None:
        if not isinstance(self.scorer, MatchingScorer):
            self.scorer = MatchingScorer(self.scorer)

        if not isinstance(self.policy, MatchingPolicy):
            self.policy = MatchingPolicy(self.policy)

        if not isinstance(self.algorithm, MatchingAlgorithm):
            self.algorithm = MatchingAlgorithm(self.algorithm)
