from __future__ import annotations

import pytest

from t4_devkit.schema import SCHEMAS as SCHEMAS_V0
from t4_devkit.schema import SchemaName as SchemaNameV0
from t4_devkit.schema.v1 import SCHEMAS, Attribute, SchemaName


def test_every_table_is_registered() -> None:
    assert set(SCHEMAS.keys()) == {name.value for name in SchemaName}
    assert SchemaName.SAMPLE.filename == "sample.json"


def test_required_tables() -> None:
    required = {name.value for name in SchemaName if not name.is_optional()}
    assert required == {"sample", "sample_data", "ego_pose", "sensor", "scene", "log", "vehicle"}


def test_registries_are_separate() -> None:
    """Each registry only accepts its own table names."""
    with pytest.raises(TypeError):
        SCHEMAS.register(SchemaNameV0.ATTRIBUTE)
    with pytest.raises(TypeError):
        SCHEMAS_V0.register(SchemaName.ATTRIBUTE)


def test_override_table_class() -> None:
    """A user can replace a table class, as documented for 0.x."""

    @SCHEMAS.register(SchemaName.ATTRIBUTE, force=True)
    class CustomAttribute(Attribute):
        pass

    try:
        assert SCHEMAS.get(SchemaName.ATTRIBUTE) is CustomAttribute
    finally:
        SCHEMAS.register(SchemaName.ATTRIBUTE, force=True)(Attribute)
