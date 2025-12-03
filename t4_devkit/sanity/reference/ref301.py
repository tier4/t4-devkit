from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName, FileFormat
from t4_devkit.dataclass.pointcloud import PointCloudMetainfo
from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe
from .base import ExternalReferenceChecker

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF301"]


@CHECKERS.register()
class REF301(ExternalReferenceChecker):
    """A checker of REF301."""

    id = RuleID("REF301")
    name = RuleName("pointcloud-metainfo-token-check")
    severity = Severity.ERROR
    description = "'PointCloudMetainfo sensor tokens' exist."
    target = SchemaName.SENSOR
    reference = "token"

    def check(self, context: SanityContext) -> list[Reason] | None:
        sensor_token_filepath = context.to_schema_file(self.target).unwrap()
        sensor_tokens = {item[self.reference] for item in load_json_safe(sensor_token_filepath).unwrap()}

        filepath = context.to_schema_file(SchemaName.SAMPLE_DATA).unwrap()
        records = load_json_safe(filepath).unwrap()
        data_root = context.data_root.unwrap()
        
        # Get all valid pointcloud info records with their filenames
        valid_records = (
            (
                record.get("info_filename", ""), 
                PointCloudMetainfo.from_file(data_root.joinpath(record.get("info_filename", ""))).source_tokens
            )
            for record in records
            if data_root.joinpath(record.get("info_filename", "")).exists()
            and record.fileformat in {FileFormat.PCD, FileFormat.PCDBIN}
        )
        
        # Flatten all source tokens with their filenames and find missing ones
        reasons = [
            Reason(f"No reference to 'Sensor.token': {token} (in {filename})")
            for filename, source_tokens in valid_records
            for token in source_tokens
            if token not in sensor_tokens
        ]
        
        return reasons