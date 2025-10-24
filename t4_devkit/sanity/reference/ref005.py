from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Any

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import ReferenceChecker

if TYPE_CHECKING:
    pass

__all__ = ["REF005"]


@CHECKERS.register(RuleID("REF005"))
class REF005(ReferenceChecker):
    """A checker of REF005."""

    name = RuleName("sample-data-to-sample")
    description = "'SampleData.sample_token' refers to 'Sample' record."
    source = SchemaName.SAMPLE_DATA
    target = SchemaName.SAMPLE
    reference = "sample_token"

    def is_additional_condition_ok(self, record: dict[str, Any]) -> bool:
        return record["is_valid"]
