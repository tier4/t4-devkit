from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.common.t4pack import FRAME_SUFFIX, PackReader, find_pack
from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe
from .base import FileReferenceChecker

if TYPE_CHECKING:
    from pathlib import Path

    from ..context import SanityContext


__all__ = ["REF201"]


@CHECKERS.register()
class REF201(FileReferenceChecker):
    """A checker of REF201."""

    id = RuleID("REF201")
    name = RuleName("sample-data-filename-presence")
    severity = Severity.ERROR
    description = "'SampleData.filename' exists as a file or in its pack."
    schema = SchemaName.SAMPLE_DATA

    def check(self, context: SanityContext) -> list[Reason] | None:
        filepath = context.to_schema_file(self.schema).unwrap()
        records = load_json_safe(filepath).unwrap()
        data_root = context.data_root.unwrap()
        packed_names: dict[str, set[str]] = {}
        return [
            Reason(f"File not found: {record['filename']}")
            for record in records
            if record.get("is_valid", True)
            and not _exists(data_root.joinpath(record["filename"]), packed_names)
        ] or None


def _exists(filepath: Path, packed_names: dict[str, set[str]]) -> bool:
    """Return whether the file exists, or is a `.pcd.bin` frame stored in its pack.

    Args:
        filepath (Path): Path to the file.
        packed_names (dict[str, set[str]]): Cache of frame names for each pack path.

    Returns:
        bool: True if the file exists.
    """
    if filepath.exists():
        return True

    if not filepath.name.endswith(FRAME_SUFFIX) or (pack_filepath := find_pack(filepath)) is None:
        return False

    if pack_filepath not in packed_names:
        try:
            with PackReader(pack_filepath) as reader:
                packed_names[pack_filepath] = set(reader.names)
        except Exception:
            packed_names[pack_filepath] = set()

    return filepath.name in packed_names[pack_filepath]
