from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .parameter import build_algorithm

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType
    from t4_devkit.evaluation import PerceptionBoxResult

    from .parameter import MatchingParams


class MatchingContext:
    """A class to construct a matching context from the matching parameters."""

    def __init__(self, params: MatchingParams) -> None:
        """Construct a new object.

        Args:
            params (MatchingParams): Matching parameters.
        """
        self._algorithm = build_algorithm(params)

    def do_matching(
        self,
        estimations: Sequence[BoxType],
        ground_truths: Sequence[BoxType],
    ) -> list[PerceptionBoxResult]:
        """Execute matching boxes.

        Args:
            estimations (Sequence[BoxType]): Sequence of estimated boxes.
            ground_truths (Sequence[BoxType]): Sequence of ground truth boxes.

        Returns:
            list[PerceptionBoxResult]: Matched results.
        """
        return self._algorithm(estimations, ground_truths)
