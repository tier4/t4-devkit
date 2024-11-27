## Generate Schema with a new token

---

You can crate a schema containing the specified table data with a new token using `new(...)` methods.

```python title="generate_attribute.py"
from t4_devkit.schema import Attribute, serialize_schema

# table data without the token field
data = {
    "name": "foo",
    "description": "this is re-generated attribute."
}

attr1 = Attribute.new(data)

# Also, it allows us to create a copy of the existing table data with a new token
serialized = serialize_schema(attr1)
attr2 = Attribute.new(serialized)

assert attr1.token != attr2.token
```

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
