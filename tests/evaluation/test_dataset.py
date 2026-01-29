from __future__ import annotations

import pytest

from t4_devkit.evaluation import EvaluationTask, load_dataset


def test_load_dataset(dummy_dataset_root) -> None:
    _ = load_dataset(dummy_dataset_root, task=EvaluationTask.DETECTION3D)

    with pytest.raises(NotImplementedError):
        _ = load_dataset(dummy_dataset_root, task=EvaluationTask.SEGMENTATION3D)
        _ = load_dataset(dummy_dataset_root, task=EvaluationTask.SEGMENTATION2D)
