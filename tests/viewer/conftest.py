import pytest

from t4_devkit.viewer import RerunViewer


@pytest.fixture(scope="module")
def dummy_viewer(label2id) -> RerunViewer:
    """Return a dummy viewer.

    Returns:
        `RerunViewer` without spawning.
    """
    return RerunViewer(
        "test_viewer",
        cameras=["camera"],
        spawn=False,
    ).with_labels(label2id=label2id)
