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


__all__ = ["REF013"]


@CHECKERS.register()
class REF013(FileReferenceChecker):
    """A checker of REF013."""

    id = RuleID("REF013")
    name = RuleName("sample-data-filename-presence")
    severity = Severity.ERROR
    description = "'SampleData.filename' exists."
    schema = SchemaName.SAMPLE_DATA

    def check(self, context: SanityContext) -> list[Reason] | None:
        filepath = context.to_schema_file(self.schema).unwrap()
        records = load_json_safe(filepath).unwrap()
        data_root = context.data_root.unwrap()
        return [
            Reason(f"File not found: {record['filename']}")
            for record in records
            if not data_root.joinpath(record["filename"]).exists()
        ] or None
