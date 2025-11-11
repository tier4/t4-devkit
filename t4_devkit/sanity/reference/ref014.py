from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe
from .base import FileReferenceChecker

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF014"]


@CHECKERS.register(RuleID("REF014"))
class REF014(FileReferenceChecker):
    """A checker of REF014."""

    name = RuleName("sample-data-filename-presence")
    severity = Severity.ERROR
    description = "'SampleData.filename' exists."
    schema = SchemaName.SAMPLE_DATA

    def check(self, context: SanityContext) -> list[Reason]:
        filepath = context.to_schema_file(self.schema).unwrap()
        records = load_json_safe(filepath).unwrap()
        data_root = context.data_root.unwrap()
        return [
            Reason(f"File not found: {record['info_filename']}")
            for record in records
            if record.get("info_filename") is not None
            and not data_root.joinpath(record["info_filename"]).exists()
        ]
