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

__all__ = ["SCH001"]


@CHECKERS.register(RuleID("SCH001"))
class SCH001(Checker):
    """A checker of SCH001."""

    name = RuleName("scene-single")
    description = "'Scene' record is a single."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.to_schema_file(SchemaName.SCENE):
            case Some(x):
                result = load_json_safe(x.as_posix())
                if not is_successful(result):
                    return [Reason("Failed to load 'Scene' file")]
                else:
                    num_scene = len(result.unwrap())
                    return (
                        []
                        if num_scene == 1
                        else [Reason(f"'Scene' must contain exactly one element: {num_scene}")]
                    )
            case _:
                return [Reason("Failed to load 'Scene' file")]
