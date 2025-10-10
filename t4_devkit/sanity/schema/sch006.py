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

__all__ = ["SCH006"]


@CHECKERS.register(RuleID("SCH006"))
class SCH006(Checker):
    """A checker of SCH006."""

    name = RuleName("instance-not-empty")
    description = "'Instance' record is not empty."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.to_schema_file(SchemaName.INSTANCE):
            case Some(x):
                result = load_json_safe(x.as_posix())
                if not is_successful(result):
                    return [Reason("Failed to load 'Instance' file")]
                else:
                    num_instance = len(result.unwrap())
                    return [] if num_instance > 0 else [Reason("No 'Instance' found")]
            case _:
                return [Reason("Failed to load 'Instance' file")]
