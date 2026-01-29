from __future__ import annotations

from attrs import define, field

from t4_devkit.filtering import FilterParams

from .matching import MatchingParams
from .task import EvaluationTask

__all__ = ["PerceptionEvaluationConfig"]


@define
class PerceptionEvaluationConfig:
    """Evaluation configuration for perception tasks."""

    dataset: str
    task: EvaluationTask = field(converter=EvaluationTask)
    filtering: FilterParams = field(default=FilterParams())
    matching: MatchingParams = field(default=MatchingParams())
