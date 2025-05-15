## Generate Schema Record with a New Token

---

You can crate a schema containing the specified table data with a new token using `new(...)` methods.

```python
>>> from t4_devkit.schema import Attribute
>>> from t4_devkit.common.serialize import serialize_dataclass
>>>
>>> # schema data except of the unique identifier token
>>> data = {
...     "name": "foo",
...     "description": "this is re-generated attribute."
... }
>>>
>>> attr1 = Attribute.new(data)
>>>
>>> # Also, it allows us to create a copy of the existing table data with a new token
>>> serialized = serialize_dataclass(attr1)
>>> attr2 = Attribute.new(serialized)
>>>
>>> attr1.token != attr2.token
True
>>> attr1
Attribute(token='b08701e5095fbd12a45e7f51b85ffc08', name='foo', description='this is re-generated attribute.')
>>> attr2
Attribute(token='f40e605870aa29b1473ca6e65255c45e', name='foo', description='this is re-generated attribute.')
```

## Customize Schema Class

---

You can customize schema classes on your own code, if you need for some reasons.

For example, you might meet the error because of missing some mandatory fields but it is OK whatever the actual value is.

In here, let's define a custom `Attribute` class, called `CustomAttribute`, in your workspace.
This class suppresses runtime exception caused by missing `description` in `attribute.json`.

Now you have the following workspace structure:

```shell
my_package
├── src
│   ├── __init__.py
│   ├── custom_schema.py
│   └── main.py
└── pyproject.toml
```

By editing `custom_schema.py`, you can define `CustomAttribute` overwriting `Attribute` as follows:

```python title="custom_schema.py"
from __future__ import annotations

from attrs import define, field

from t4_devkit.schema import SCHEMAS, SchemaName, SchemaBase
from t4_devkit.common.io import load_json

__all__ = ["CustomAttribute"]


@define(slots=False)
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

Note that `CustomAttribute` should be imported before instantiating `Tier4` class.
Then modify `__init__.py` in order to import it automatically:

```python title="__init__.py"
from .custom_attribute import * # noqa
```
