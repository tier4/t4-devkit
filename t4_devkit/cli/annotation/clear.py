from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from returns.result import Failure, Result, Success

from t4_devkit import T4Devkit
from t4_devkit.schema import SchemaName

__all__ = [
    "AnnotationClearError",
    "ClearOutcome",
    "ClearPlan",
    "clear_annotations",
    "plan_clear_annotations",
]


class AnnotationClearError(RuntimeError):
    """Raised when annotation records cannot be cleared."""


@dataclass(frozen=True)
class ClearPlan:
    """Description of an annotation clear operation."""

    source_root: Path
    target_root: Path
    schemas: tuple[SchemaName, ...]
    new_version: bool


@dataclass(frozen=True)
class ClearOutcome:
    """Result of an annotation clear operation."""

    target_root: Path
    schemas: tuple[SchemaName, ...]
    version_created: bool


def plan_clear_annotations(
    data_root: str,
    *,
    revision: str | None = None,
    new_version: bool = False,
    exclude: list[str] | None = None,
) -> Result[ClearPlan, AnnotationClearError]:
    """Validate inputs and create a plan for clearing annotation records."""
    try:
        t4 = T4Devkit(data_root, revision=revision, verbose=False)
    except (FileNotFoundError, NotADirectoryError):
        return Failure(AnnotationClearError(f"Dataset root is not found: {data_root}"))

    annotation_dir = Path(t4.annotation_dir)
    if not annotation_dir.is_dir():
        return Failure(AnnotationClearError(f"Annotation directory is not found: {annotation_dir}"))

    try:
        excluded_schemas = _resolve_excluded_schemas(exclude)
    except AnnotationClearError as error:
        return Failure(error)
    schemas = tuple(
        schema for schema in SchemaName if schema.is_annotated() and schema not in excluded_schemas
    )
    target_root = _next_version_path(Path(data_root)) if new_version else Path(t4.data_root)
    return Success(
        ClearPlan(
            source_root=Path(t4.data_root),
            target_root=target_root,
            schemas=schemas,
            new_version=new_version,
        )
    )


def clear_annotations(plan: ClearPlan) -> Result[ClearOutcome, AnnotationClearError]:
    """Execute an annotation clear plan without prompting or writing CLI output."""
    if plan.new_version:
        version_created = False
        try:
            _copy_version(plan.source_root, plan.target_root)
            version_created = True
            _clear_annotation_tables(plan.target_root / "annotation", plan.schemas)
        except OSError as error:
            if version_created:
                shutil.rmtree(plan.target_root, ignore_errors=True)
            return Failure(
                AnnotationClearError(f"Failed to create version '{plan.target_root.name}': {error}")
            )
    else:
        try:
            _clear_annotation_tables(plan.target_root / "annotation", plan.schemas)
        except OSError as error:
            return Failure(AnnotationClearError(f"Failed to clear annotation records: {error}"))

    return Success(
        ClearOutcome(
            target_root=plan.target_root,
            schemas=plan.schemas,
            version_created=plan.new_version,
        )
    )


# === Private helpers ===


def _resolve_excluded_schemas(exclude: list[str] | None) -> set[SchemaName]:
    excluded_schemas: set[SchemaName] = set()
    for name in exclude or []:
        try:
            schema = SchemaName(name.removesuffix(".json"))
        except ValueError as error:
            raise AnnotationClearError(f"Unknown schema name: {name}") from error
        if not schema.is_annotated():
            raise AnnotationClearError(f"Schema is not an annotation table: {name}")
        excluded_schemas.add(schema)
    return excluded_schemas


def _next_version_path(data_root: Path) -> Path:
    """Return the path for the next numeric dataset version."""
    versions = [
        int(path.name) for path in data_root.iterdir() if path.is_dir() and path.name.isdigit()
    ]
    return data_root / str(max(versions, default=-1) + 1)


def _copy_version(source: Path, destination: Path) -> None:
    """Copy a dataset into a new version directory without recursively copying itself."""
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")

    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent.parent)
    )
    staging_version = staging_root / destination.name
    try:
        shutil.copytree(source, staging_version)
        os.replace(staging_version, destination)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def _clear_annotation_tables(
    annotation_dir: Path, annotated_schemas: tuple[SchemaName, ...]
) -> None:
    """Replace annotation tables with empty JSON arrays."""
    for schema in annotated_schemas:
        _save_empty_table(annotation_dir / schema.filename)


def _save_empty_table(filepath: Path) -> None:
    """Atomically replace an annotation table with an empty JSON array."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=filepath.parent, prefix=f".{filepath.name}.", delete=False
        ) as file:
            json.dump([], file, ensure_ascii=False, indent=4)
            file.write("\n")
            temporary_path = Path(file.name)
        os.replace(temporary_path, filepath)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
