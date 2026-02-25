from __future__ import annotations

from t4_devkit.evaluation import EvaluationTask


def test_task() -> None:
    task_names = {
        "detection3d",
        "tracking3d",
        "prediction3d",
        "segmentation3d",
        "detection2d",
        "tracking2d",
        "segmentation2d",
    }

    assert task_names == {e.value for e in EvaluationTask}

    for name in task_names:
        task = EvaluationTask(name)

        assert task == name
        if name in ("detection3d", "tracking3d", "prediction3d", "segmentation3d"):
            assert task.is_3d()
        elif name in ("detection2d", "tracking2d", "segmentation2d"):
            assert task.is_2d()
        else:
            raise ValueError(f"{name} doesn't have an indicator")

        if name in ("segmentation3d", "segmentation2d"):
            assert task.is_segmentation()
