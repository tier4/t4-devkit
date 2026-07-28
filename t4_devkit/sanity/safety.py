from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import safe

from t4_devkit import DBMetadata, T4Devkit, load_metadata
from t4_devkit.common import load_json, save_json

if TYPE_CHECKING:
    from t4_devkit.schema import SchemaBase
    from t4_devkit.typing import PathLike

    from .context import SanityContext


@safe
def load_json_safe(filename: PathLike) -> list[dict]:
    """Load JSON file safely."""
    return load_json(filename)


@safe
def save_json_safe(data: list[dict], filename: PathLike) -> None:
    """Save JSON file safely."""
    return save_json(data, filename)


@safe
def load_schema_safe(module: type[SchemaBase], record: dict) -> SchemaBase:
    """Load schema from dict safely."""
    return module.from_dict(record)


@safe
def load_metadata_safe(data_root: PathLike, revision: str | None = None) -> DBMetadata:
    """Load DBMetadata safely."""
    return load_metadata(data_root, revision=revision)


@safe
def load_tier4_safe(context: SanityContext) -> T4Devkit:
    """Load T4Devkit instance safely."""
    data_root = context.data_root.unwrap()
    revision = context.version.value_or(None)
    data_root = data_root.as_posix() if revision is None else data_root.parent.as_posix()
    return T4Devkit(data_root, revision=revision, verbose=False)
