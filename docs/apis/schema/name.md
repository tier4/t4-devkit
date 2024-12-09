Under the hood, `t4-devkit` declares an enum called `SchemaName`.
This enum includes names of each schema table that should be contained in the T4 dataset as `.json` file.

Note that some schema tables are not mandatory, such as `object_ann.json` and `surface_ann.json`.
For these tables, the method called `is_optional()` returns `True` and it is OK that these corresponding `.json` files are not contained in T4 dataset:

```python
from t4_devkit.schema import SchemaName

>>> SchemaName.OBJECT_ANN.is_optional()
True
```

<!-- prettier-ignore-start -->

::: t4_devkit.schema.name
    options:
        show_docstring_attributes: true
        show_bases: false

<!-- prettier-ignore-end -->
