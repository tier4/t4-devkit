## Perception Evaluation

```python
from t4_devkit.evaluation import PerceptionEvaluator, PerceptionConfig, EvaluationTask

config = PerceptionConfig(
    dataset="<PATH_TO_DATASET>",
    task=EvaluationTask.<TASK_ENUM>,
)

evaluator = PerceptionEvaluator(config)
```

## Sensing Evaluation

TBD
