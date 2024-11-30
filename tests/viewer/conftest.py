import pytest

from t4_devkit.viewer import Tier4Viewer


@pytest.fixture(scope="module")
def dummy_viewer(label2id) -> Tier4Viewer:
    """Return a dummy viewer.

    Returns:
        `Tier4Viewer` without spawning.
    """
    return Tier4Viewer("test_viewer", cameras=["camera"], spawn=False).with_labels(
        label2id=label2id
    )
