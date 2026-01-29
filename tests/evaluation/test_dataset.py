from __future__ import annotations

from t4_devkit.evaluation import EvaluationTask, load_dataset


def test_load_dataset(dummy_dataset_root) -> None:
    for task in EvaluationTask:
        _ = load_dataset(dummy_dataset_root, task=task)
