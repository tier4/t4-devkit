## Sanity Check

### Quick Start

`sanity_check(...)` function performs a series of sanity checks to ensure the integrity of the dataset.

About the defined rules, please refer to [requirement.md](../schema/requirement.md).

```python title="main.py"
from t4_devkit.common import save_json, serialize_dataclass
from t4_devkit.sanity import sanity_check, print_sanity_result


result = sanity_check("<path/to/dataset>")

# display detailed results and summary
print_sanity_result(result)

# save result to JSON file if you want
save_json(serialize_dataclass(result), "result.json")
```

### How to Add New Checkers

All checkers must follow:

- Implement a class that inherits from `Checker` class.
- Its ID must be unique and belong to one of `RuleGroup` enum.
- Override the `check() -> list[Reason] | None` method to perform the specific check.
- Register the checker using `CHECKERS.register()` decorator.

```python title="str000.py"
from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.sanity.checker import Checker, RuleID, RuleName, Severity
from t4_devkit.sanity.registry import CHECKERS
from t4_devkit.sanity.result import Reason

if TYPE_CHECKING:
    from t4_devkit.sanity.context import SanityContext


@CHECKERS.register()
class STR000(Checker):
    """This is a custom checker."""

    id = RuleID("STR000")
    name = RuleName("my-custom-checker")
    severity = Severity.ERROR
    description = "This is a custom checker."

    def check(self, context: SanityContext) -> list[Reason] | None:
        # Return a list of reasons if the check fails, or None if it passes.
        return None
```
