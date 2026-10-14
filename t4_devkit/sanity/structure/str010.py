from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from t4_devkit.schema.v1 import MANIFEST_FILENAME, SUPPORTED_SCHEMA_MAJOR_VERSION

from ..checker import Checker, RuleID, RuleName, SchemaVersion, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR010"]


@CHECKERS.register()
class STR010(Checker):
    """A checker of STR010."""

    id = RuleID("STR010")
    name = RuleName("schema-version-supported")
    severity = Severity.ERROR
    description = (
        "'manifest.json' declares a supported 'schema_version' (major version 1). "
        "If not, no other 1.0 rule runs."
    )
    versions = (SchemaVersion.V1,)

    def check(self, context: SanityContext) -> list[Reason] | None:
        match context.raw_manifest:
            case Some(manifest):
                version = manifest.get("schema_version") if isinstance(manifest, dict) else None
                if not isinstance(version, str):
                    return [Reason(f"'schema_version' is missing or not a string: {version!r}")]
                if version.split(".")[0] != str(SUPPORTED_SCHEMA_MAJOR_VERSION):
                    return [Reason(f"Unsupported 'schema_version': {version}")]
                return None
        return [Reason(f"'{MANIFEST_FILENAME}' cannot be read")]
