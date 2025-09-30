from __future__ import annotations

import pytest

from t4_devkit.viewer import RerunViewer, ViewerBuilder


@pytest.fixture(scope="session")
def dummy_viewer(tmpdir_factory, spawn_viewer, label2id) -> RerunViewer:
    """Return a dummy viewer.

    Returns:
        `RerunViewer` without spawning.
    """
    save_dir = None if spawn_viewer else tmpdir_factory.mktemp("sample_recording")

    return (
        ViewerBuilder()
        .with_spatial3d()
        .with_spatial2d(["camera"])
        .with_labels(label2id)
        .build("test_viewer", save_dir=save_dir)
    )
