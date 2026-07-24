## Perception Evaluation

```python
from t4_devkit.evaluation import PerceptionEvaluator, PerceptionEvaluationConfig, EvaluationTask

config = PerceptionEvaluationConfig(
    dataset="<PATH_TO_DATASET>",
    task=EvaluationTask.<TASK_ENUM>,
)

evaluator = PerceptionEvaluator(config)
```

## Sensing Evaluation

TBD
