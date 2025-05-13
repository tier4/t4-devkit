from __future__ import annotations

import pytest

from t4_devkit.viewer import RerunViewer


@pytest.fixture(scope="session")
def dummy_viewer(tmpdir_factory, spawn_viewer, label2id) -> RerunViewer:
    """Return a dummy viewer.

    Returns:
        `RerunViewer` without spawning.
    """
    save_dir = None if spawn_viewer else tmpdir_factory.mktemp("sample_recording")

    return RerunViewer(
        "test_viewer",
        cameras=["camera"],
        save_dir=save_dir,
    ).with_labels(label2id=label2id)
