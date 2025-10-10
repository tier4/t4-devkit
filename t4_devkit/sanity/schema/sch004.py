from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some
from returns.pipeline import is_successful

from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["SCH004"]


@CHECKERS.register(RuleID("SCH004"))
class SCH004(Checker):
    """A checker of SCH004."""

    name = RuleName("ego-pose-not-empty")
    description = "'EgoPose' record is not empty."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.to_schema_file(SchemaName.EGO_POSE):
            case Some(x):
                result = load_json_safe(x.as_posix())
                if not is_successful(result):
                    return [Reason("Failed to load 'EgoPose' file")]
                else:
                    num_ego_pose = len(result.unwrap())
                    return [] if num_ego_pose > 0 else [Reason("No 'EgoPose' found")]
            case _:
                return [Reason("Failed to load 'EgoPose' file")]
