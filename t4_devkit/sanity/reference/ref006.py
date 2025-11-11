from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF006"]


@CHECKERS.register(RuleID("REF006"))
class REF006(RecordReferenceChecker):
    """A checker of REF006."""

    name = RuleName("sample-data-to-ego-pose")
    description = "'SampleData.ego_pose_token' refers to 'EgoPose' record."
    source = SchemaName.SAMPLE_DATA
    target = SchemaName.EGO_POSE
    reference = "ego_pose_token"
