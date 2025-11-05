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


@CHECKERS.register(RuleID("REF013"))
class REF013(FileReferenceChecker):
    """A checker of REF013."""

    name = RuleName("sample-data-info-filename-presence")
    description = "'SampleData.info_filename' exists."

    schema = SchemaName.SAMPLE_DATA

    def check(self, context: SanityContext) -> list[Reason]:
        filepath = context.to_schema_file(self.schema).unwrap()
        records = load_json_safe(filepath).unwrap()
        match context.data_root:
            case Some(x):
                reasons = [
                    Reason(f"File not found: {record['info_filename']}")
                    for record in records
                    if record.get("info_filename") is not None
                    and not x.joinpath(record["info_filename"]).exists()
                ]
                return reasons
            case _:
                return [Reason("Missing sensor data directory.")]
