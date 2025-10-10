from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["REF005"]


@CHECKERS.register(RuleID("REF005"))
class REF005(Checker):
    """A checker of REF005."""

    name = RuleName("sample-data-to-sample")
    description = "'SampleData.sample_token' refers to 'Sample' record."

    def check(self, context: SanityContext) -> list[Reason]:
        sample_data_file = context.to_schema_file(SchemaName.SAMPLE_DATA)
        sample_file = context.to_schema_file(SchemaName.SAMPLE)
        match (sample_data_file, sample_file):
            case Some(x), Some(y):
                sample_data = load_json_safe(x).unwrap()
                sample_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(f"No reference to 'SampleData.sample_token': {s['sample_token']}")
                    for s in sample_data
                    if s["sample_token"] not in sample_tokens and s["is_valid"]
                ]
            case _:
                return [Reason("Missing 'SampleData' or 'Sample' file")]
