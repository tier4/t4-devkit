from __future__ import annotations

from typing import TYPE_CHECKING

from collections import defaultdict

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC013"]


@CHECKERS.register()
class REC013(RecordsChecker):
    """A checker of REC013."""

    id = RuleID("REC013")
    name = RuleName("instance-annotation-count")
    severity = Severity.ERROR
    description = (
        "'Instance.nbr_annotations' equals the number of its 'SampleAnnotation' and 'ObjectAnn' "
        "records, and its first / last annotation tokens point to its first / last one in time."
    )
    tables = (
        SchemaName.INSTANCE,
        SchemaName.SAMPLE,
        SchemaName.SAMPLE_DATA,
        SchemaName.SAMPLE_ANNOTATION,
        SchemaName.OBJECT_ANN,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        expected = _expected_annotations(context)
        failures = []
        for instance in context.load_records(SchemaName.INSTANCE).unwrap():
            count, first, last = expected.get(instance.token, (0, None, None))
            if instance.nbr_annotations != count:
                failures.append(
                    Reason(
                        f"Instance {instance.token}: 'nbr_annotations' {instance.nbr_annotations}, has {count}"
                    )
                )
            if (instance.first_annotation_token, instance.last_annotation_token) != (first, last):
                failures.append(
                    Reason(
                        f"Instance {instance.token}: first / last annotation "
                        f"{instance.first_annotation_token} / {instance.last_annotation_token}, "
                        f"expected {first} / {last}"
                    )
                )
        return failures or None

    def fix(self, context: SanityContext) -> bool:
        expected = _expected_annotations(context)
        records = context.load_table(SchemaName.INSTANCE).unwrap()
        for record in records:
            count, first, last = expected.get(record["token"], (0, None, None))
            record["nbr_annotations"] = count
            record["first_annotation_token"] = first
            record["last_annotation_token"] = last
        return context.save_table(SchemaName.INSTANCE, records)


def _expected_annotations(context: SanityContext) -> dict[str, tuple[int, str, str]]:
    """Count, first and last annotation token in time of each instance with annotations.

    A `SampleAnnotation` is at its sample's time, an `ObjectAnn` at its frame's time.
    """
    samples = {sample.token: sample for sample in context.load_records(SchemaName.SAMPLE).unwrap()}
    frames = {frame.token: frame for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap()}
    times: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for ann in context.load_records(SchemaName.SAMPLE_ANNOTATION).unwrap():
        if ann.sample_token in samples:
            times[ann.instance_token].append((samples[ann.sample_token].timestamp, ann.token))
    for ann in context.load_records(SchemaName.OBJECT_ANN).unwrap():
        if ann.instance_token is not None and ann.sample_data_token in frames:
            times[ann.instance_token].append((frames[ann.sample_data_token].timestamp, ann.token))
    return {
        token: (len(entries), min(entries)[1], max(entries)[1]) for token, entries in times.items()
    }
