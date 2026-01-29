"""Compatibility helpers that abstract away differences between T4Dataset revisions."""

from __future__ import annotations

from t4_devkit.schema import Category


def fix_category_table(categories: list[Category]) -> list[Category]:
    """Fix unpopulated index fields in some T4Dataset revisions.

    This function behaves differently in the below three cases:

    - All `index` fields are set: the list is returned unmodified.
    - All `index` fields are `None`: the position of each category in the list is used to compute
      `index`. The resulting indices start at `0`.
    - Some `index` fields are set and some are `None`: raise a `ValueError`.

    Args:
        categories (list[Category]): List of categories to fix.

    Returns:
        list[Category]: Fixed list of categories.

    Raises:
        ValueError: If the `index` field is set for some categories and `None` for others.
    """
    if any(category.index is None for category in categories):
        if not all(category.index is None for category in categories):
            raise ValueError("Category index is not set for some categories.")

        for idx, category in enumerate(categories):
            category.index = idx
    return categories
