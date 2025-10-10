from __future__ import annotations

from returns.pipeline import is_successful
from returns.result import safe

from t4_devkit.schema import SCHEMAS, SchemaName, SchemaBase

from ..result import Reason


def build_records(schema: SchemaName, records: list[dict]) -> list[Reason]:
    module = SCHEMAS.get(schema)
    failures = []
    for record in records:
        conversion = _safe_from_dict(module, record)
        if not is_successful(conversion):
            failures.append(Reason(f"[{schema.name}] {record['token']}: {conversion.failure()}"))
    return failures


@safe
def _safe_from_dict(module: SchemaBase, record: dict):
    return module.from_dict(record)
