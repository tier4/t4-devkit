from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from t4_devkit.sanity import sanity_check
from t4_devkit.schema.v1 import NewVersion, SchemaName, load_dataset
from tests.helpers import SAMPLE_V0, SAMPLE_V1


def _source(tmp_path: Path) -> Path:
    """The 1.0 sample as `<tmp_path>/sample/0`, so that links stay on one file system."""
    root = tmp_path / "sample" / "0"
    shutil.copytree(SAMPLE_V1, root)
    return root


def test_new_version(tmp_path: Path) -> None:
    """Version 1 from version 0: data files hard-linked, an edited table written, the manifest
    carried over with a history entry, and the 1.0 rules pass."""
    source_root = _source(tmp_path)
    new = NewVersion(source_root, tmp_path / "sample" / "1", changes="test: descriptions edited")
    for category in new.tables[SchemaName.CATEGORY]:
        category.description = "edited"
    manifest = new.save()

    assert (manifest.version, manifest.created_at) == (1, new.source.manifest.created_at)
    (entry,) = manifest.history
    assert (entry.version, entry.from_version, entry.changes) == (1, 0, "test: descriptions edited")
    assert new.linked == len(manifest.assets) > 0
    for asset in manifest.assets:
        linked = (tmp_path / "sample" / "1" / asset.path).stat()
        assert linked.st_ino == (source_root / asset.path).stat().st_ino

    dataset = load_dataset(tmp_path / "sample" / "1")
    assert all(c.description == "edited" for c in dataset.tables[SchemaName.CATEGORY])
    reports = sanity_check((tmp_path / "sample").as_posix(), revision="1").reports
    assert not [report.id for report in reports if report.is_failed()]


def test_new_version_copied_with_given_version(tmp_path: Path) -> None:
    """`link=False` copies the files, the version can be given, and the history accumulates."""
    source_root = _source(tmp_path)
    NewVersion(source_root, tmp_path / "sample" / "1", changes="first").save()
    new = NewVersion(
        tmp_path / "sample" / "1",
        tmp_path / "sample" / "7",
        changes="second",
        version=7,
        link=False,
    )
    manifest = new.save()

    assert manifest.version == 7
    assert [(e.version, e.from_version, e.changes) for e in manifest.history] == [
        (1, 0, "first"),
        (7, 1, "second"),
    ]
    assert new.linked == 0
    for asset in manifest.assets:
        copied, original = tmp_path / "sample" / "7" / asset.path, source_root / asset.path
        assert copied.stat().st_ino != original.stat().st_ino
        assert copied.read_bytes() == original.read_bytes()


def test_new_version_needs_a_manifest(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="0.x"):
        NewVersion(SAMPLE_V0, tmp_path / "out", changes="x")
