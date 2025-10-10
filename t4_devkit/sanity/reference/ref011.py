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

__all__ = ["REF011"]


@CHECKERS.register(RuleID("REF011"))
class REF011(Checker):
    """A checker of REF011."""

    name = RuleName("instance-to-last-sample-annotation")
    description = "'Instance.last_annotation_token' refers to 'SampleAnnotation' record."

    def check(self, context: SanityContext) -> list[Reason]:
        instance_file = context.to_schema_file(SchemaName.INSTANCE)
        sample_ann_file = context.to_schema_file(SchemaName.SAMPLE_ANNOTATION)
        match (instance_file, sample_ann_file):
            case Some(x), Some(y):
                instance = load_json_safe(x).unwrap()
                sample_ann_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(
                        f"No reference to `Instance.last_annotation_token`: {ins['last_annotation_token']}"
                    )
                    for ins in instance
                    if ins["last_annotation_token"] not in sample_ann_tokens
                ]
            case _:
                return [Reason("Missing `Instance` or `SampleAnnotation` file")]
