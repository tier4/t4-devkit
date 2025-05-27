from __future__ import annotations

from attrs import define, field

from t4_devkit.filtering import FilterParams

from .matching import MatchingParams
from .task import EvaluationTask

__all__ = ["PerceptionConfig"]


@define
class PerceptionConfig:
    """Evaluation configuration for perception tasks."""

    dataset: str
    task: EvaluationTask = field(converter=EvaluationTask)
    filtering: FilterParams = field(default=FilterParams())
    matching: MatchingParams = field(default=MatchingParams())
