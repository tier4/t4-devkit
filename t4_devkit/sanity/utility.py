from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Result, safe

if TYPE_CHECKING:
    from t4_devkit import Tier4
    from t4_devkit.schema import SchemaTable


@safe
def lookup_table(t4: Tier4, table_name: str, token: str) -> Result[SchemaTable, Exception]:
    """Try to return a schema table object without any exceptions.

    Args:
        t4 (Tier4): The Tier4 instance.
        table_name (str): The name of the table to look up.
        token (str): The token to use for authentication.

    Returns:
        The result of the lookup operation.
    """
    return t4.get(table_name, token)
