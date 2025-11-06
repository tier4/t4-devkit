from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import RecordReferenceChecker


__all__ = ["REF012"]


@CHECKERS.register(RuleID("REF012"))
class REF012(RecordReferenceChecker):
    """A checker of REF012."""

    name = RuleName("lidarset-to-sample-data")
    description = "'LidarSeg.sample_data_token' refers to 'SampleData' record."
    source = SchemaName.LIDARSEG
    target = SchemaName.SAMPLE_DATA
    reference = "sample_data_token"
