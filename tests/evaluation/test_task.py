from __future__ import annotations

from t4_devkit.evaluation import EvaluationTask


def test_task() -> None:
    task_names = {"detection3d", "tracking3d", "prediction3d", "detection2d", "tracking2d"}

    assert task_names == {e.value for e in EvaluationTask}

    for name in task_names:
        task = EvaluationTask(name)

        assert task == name
