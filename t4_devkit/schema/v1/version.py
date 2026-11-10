"""A new version of a dataset from an existing one."""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from t4_devkit.common.serialize import serialize_dataclass

from .loader import load_dataset
from .writer import DatasetWriter

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

    from .manifest import Manifest

__all__ = ["NewVersion"]


class NewVersion:
    """Version N+1 of a dataset from version N: the data files linked, the tables loaded for
    editing, the manifest carried over with a `history` entry.

    The caller changes `tables` (e.g. replaces the labels of one task), then `save` writes them
    and `manifest.json`. The files under `data/`, `map/` and `input_bag/` are hard-linked, so a
    new version costs no sensor data space; where a link is not possible (another file system)
    the file is copied, and `link=False` copies everything. Versions are never changed in place,
    so linked files stay identical.

    Examples:
        >>> new = NewVersion("<DATASET_ID>/3", "out/<DATASET_ID>/4", changes="kognic_to_t4: detection3d labels replaced")
        >>> new.tables[SchemaName.SAMPLE_ANNOTATION] = annotations
        >>> manifest = new.save()
    """

    def __init__(
        self,
        source_root: PathLike,
        output_root: PathLike,
        changes: str,
        *,
        version: int | None = None,
        link: bool = True,
    ) -> None:
        """
        Args:
            source_root (PathLike): The version to start from, `<DATASET_ID>/<N>`.
            output_root (PathLike): The version to create, `<DATASET_ID>/<N+1>`; must not exist.
            changes (str): What this version changes, for `manifest.history`.
            version (int | None, optional): Version of the new dataset (given by Web.Auto); the
                source's plus one by default.
            link (bool, optional): Hard-link the data files instead of copying them.

        Raises:
            ValueError: If the source is a 0.x dataset: migrate it first.
            FileExistsError: If `output_root` exists.
        """
        self.source = load_dataset(source_root)
        if self.source.manifest is None:
            raise ValueError(f"{source_root} is a 0.x dataset: migrate it before a new version")
        self.writer = DatasetWriter(output_root)
        self.tables = self.source.tables
        self.version = self.source.manifest.version + 1 if version is None else version
        self.changes = changes
        self.linked = self._link_assets(Path(source_root), link)

    def save(self) -> Manifest:
        """Write the tables and `manifest.json` of the new version.

        Returns:
            The manifest written.
        """
        return self.writer.save(self.tables, self.manifest_info())

    def manifest_info(self) -> dict[str, Any]:
        """Return the manifest fields of the new version: the source's, with the new `version`
        and a `history` entry. `created_at` stays the dataset's creation time; files and
        capabilities are recomputed by the writer."""
        info = serialize_dataclass(self.source.manifest)
        for name in ("tables", "assets", "capabilities"):
            del info[name]
        entry = {
            "version": self.version,
            "from_version": self.source.manifest.version,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "changes": self.changes,
        }
        info["version"] = self.version
        info["history"] = list(info["history"] or []) + [entry]
        return info

    def _link_assets(self, source_root: Path, link: bool) -> int:
        """Link, or copy, every file the source manifest lists as an asset.

        Returns:
            The number of files linked (the others were copied).
        """
        linked = 0
        for entry in self.source.manifest.assets:
            source = source_root / entry.path
            destination = self.writer.output_root / entry.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if link:
                try:
                    os.link(source, destination)
                    linked += 1
                    continue
                except OSError:  # another file system, or no hard links
                    pass
            shutil.copy2(source, destination)
        return linked
