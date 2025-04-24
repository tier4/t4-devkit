## Generate Schema Record with a New Token

---

You can crate a schema containing the specified table data with a new token using `new(...)` methods.

```python title="generate_attribute.py"
from t4_devkit.schema import Attribute
from t4_devkit.common.serialize import serialize_dataclass

# schema data except of the unique identifier token
data = {
    "name": "foo",
    "description": "this is re-generated attribute."
}

attr1 = Attribute.new(data)

# Also, it allows us to create a copy of the existing table data with a new token
serialized = serialize_dataclass(attr1)
attr2 = Attribute.new(serialized)

assert attr1.token != attr2.token
```

## Customize Schema Class

---

You can customize schema classes on your own code, if you need for some reasons.

For example, you might meet the error because some mandatory field but you are OK whatever the actual value is.

In here, let's define a custom `Attribute` class, called `CustomAttribute`, in your workspace.
This class allows it is OK even `description` field is not recorded in `attribute.json`.

Now you have the following workspace structure:

```shell
my_package
├── src
│   ├── __init__.py
│   ├── custom_attribute.py
│   └── main.py
└── pyproject.toml
```

By editing `custom_attribute.py`, you can customize `Attribute` as follows:

```python title="custom_attribute.py"
from __future__ import annotations

from attrs import define, field

from t4_devkit.schema import SCHEMAS, SchemaName, SchemaBase
from t4_devkit.common.io import load_json

__all__ = ["CustomAttribute"]


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

Note that `CustomAttribute` should be imported before to instantiate `Tier4` class.
Then modify `__init__.py` in order to import it automatically:

```python title="__init__.py"
from .custom_attribute import * # noqa
```
