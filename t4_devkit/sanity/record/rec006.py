from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe
from .base import RecordCountChecker

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["REC006"]


@CHECKERS.register()
class REC006(RecordCountChecker):
    """A checker of REC006."""

    id = RuleID("REC006")
    name = RuleName("instance-not-empty")
    severity = Severity.ERROR
    description = (
        "'Instance' record is not empty if either 'SampleAnnotation' or 'ObjectAnn' is not empty."
    )
    schema = SchemaName.INSTANCE

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        # return skip reason if instance.json does not exist
        match super().can_skip(context):
            case Some(x):
                return Maybe.from_value(x)

        # instance.json should contain any records if either
        # SampleAnnotation or ObjectAnn records exist
        sample_ann_file = context.to_schema_file(SchemaName.SAMPLE_ANNOTATION)
        object_ann_file = context.to_schema_file(SchemaName.OBJECT_ANN)

        match (sample_ann_file.value_or(None), object_ann_file.value_or(None)):
            case (None, _) | (_, None):
                return Maybe.from_value(Reason("Missing 'annotation' directory"))
            case (s, o):
                sample_ann_count = len(load_json_safe(s).unwrap()) if s.exists() else 0
                object_ann_count = len(load_json_safe(o).unwrap()) if o.exists() else 0
                return (
                    Maybe.from_value(
                        Reason(
                            f"Both {SchemaName.SAMPLE_ANNOTATION} "
                            f"and {SchemaName.OBJECT_ANN} records are empty"
                        )
                    )
                    if sample_ann_count == 0 and object_ann_count == 0
                    else Nothing
                )

    def check_count(self, records: list[dict]) -> list[Reason] | None:
        num_instance = len(records)
        return [Reason("'Instance' record must not be empty")] if num_instance == 0 else None
