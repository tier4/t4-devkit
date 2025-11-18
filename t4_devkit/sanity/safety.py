from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Result, safe

from t4_devkit import DBMetadata, Tier4, load_metadata
from t4_devkit.common.io import load_json

if TYPE_CHECKING:
    from t4_devkit.schema import SchemaBase

    from .context import SanityContext


@safe
def load_json_safe(filename: str) -> Result[list[dict], Exception]:
    """Load JSON file safely."""
    return load_json(filename)


@safe
def load_schema_safe(module: type[SchemaBase], record: dict) -> Result[SchemaBase, Exception]:
    """Load schema from dict safely."""
    return module.from_dict(record)


@safe
def load_metadata_safe(
    data_root: str,
    revision: str | None = None,
) -> Result[DBMetadata, Exception]:
    """Load DBMetadata safely."""
    return load_metadata(data_root, revision=revision)


@safe
def load_tier4_safe(context: SanityContext) -> Result[Tier4, Exception]:
    """Load Tier4 instance safely."""
    data_root = context.data_root.unwrap()
    revision = context.version.value_or(None)
    data_root = data_root.as_posix() if revision is None else data_root.parent.as_posix()
    return Tier4(data_root, revision=revision, verbose=False)
