from __future__ import annotations

from t4_devkit.schema.tables.registry import SchemaRegistry

from .name import SchemaName

__all__ = ["SCHEMAS"]

SCHEMAS = SchemaRegistry(SchemaName)
