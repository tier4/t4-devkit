from __future__ import annotations

import pytest

from t4_devkit.viewer import RerunViewer


@pytest.fixture(scope="module")
def dummy_viewer(spawn_viewer, label2id) -> RerunViewer:
    """Return a dummy viewer.

    Returns:
        `RerunViewer` without spawning.
    """
    return RerunViewer(
        "test_viewer",
        cameras=["camera"],
        spawn=spawn_viewer,  # set this to True for debugging
    ).with_labels(label2id=label2id)
