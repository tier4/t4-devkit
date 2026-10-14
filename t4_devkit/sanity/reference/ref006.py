from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, SchemaVersion, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF006"]


@CHECKERS.register()
class REF006(RecordReferenceChecker):
    """A checker of REF006."""

    id = RuleID("REF006")
    name = RuleName("sample-data-to-ego-pose")
    severity = Severity.ERROR
    versions = (SchemaVersion.V0, SchemaVersion.V1)
    description = "'SampleData.ego_pose_token' refers to 'EgoPose' record."
    source = SchemaName.SAMPLE_DATA
    target = SchemaName.EGO_POSE
    reference = "ego_pose_token"
