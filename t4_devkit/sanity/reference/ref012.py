from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe
from .base import FileReferenceChecker

if TYPE_CHECKING:
    from ..context import SanityContext


@CHECKERS.register(RuleID("REF012"))
class REF012(FileReferenceChecker):
    """A checker of REF012."""

    name = RuleName("sample-data-filename-presence")
    description = "'SampleData.filename' exists."

    schema = SchemaName.SAMPLE_DATA

    def check(self, context: SanityContext) -> list[Reason]:
        filepath = context.to_schema_file(self.schema).unwrap()
        records = load_json_safe(filepath).unwrap()
        match context.data_root:
            case Some(x):
                reasons = [
                    Reason(f"File not found: {record['filename']}")
                    for record in records
                    if not x.joinpath(record["filename"]).exists()
                ]
                return reasons
            case _:
                return [Reason("Missing sensor data directory.")]
