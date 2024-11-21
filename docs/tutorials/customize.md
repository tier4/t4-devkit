## Customize Schema

---

You can customize schema classes on your own code, if you need for some reasons.

For example, you can make `Attribute` allow `attribute.json` not to require `description` field as follows:

```python title="custom_attribute.py"
from attrs import define, field
from typing import Any

from typing_extensions import Self

from t4_devkit.schema import SCHEMAS, SchemaName, SchemaBase
from t4_devkit.common.io import load_json


@define
@SCHEMAS.register(SchemaName.ATTRIBUTE, force=True)
class CustomAttribute(SchemaBase):
    """Custom Attribute class ignoring if there is no `description` field.
    Note that `description` field is mandatory in the original `Attribute` class.

    `@SCHEMAS.register(SchemaName.ATTRIBUTE, force=True)` performs that
    it forces to update the attribute table in the schema registry.
    """

    name: str
    description: str | None = field(default=None)
```
