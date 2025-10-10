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

__all__ = ["SCH003"]


@CHECKERS.register(RuleID("SCH003"))
class SCH003(Checker):
    """A checker of SCH003."""

    name = RuleName("sample-data-not-empty")
    description = "'SampleData' record is not empty."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.to_schema_file(SchemaName.SAMPLE_DATA):
            case Some(x):
                result = load_json_safe(x.as_posix())
                if not is_successful(result):
                    return [Reason("Failed to load 'SampleData' file")]
                else:
                    num_sample_data = len(result.unwrap())
                    return [] if num_sample_data > 0 else [Reason("No 'SampleData' found")]
            case _:
                return [Reason("Failed to load 'SampleData' file")]
