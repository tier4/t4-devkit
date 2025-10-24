from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from enum import Enum, unique

from .checker import Checker, RuleID


@unique
class RuleGroup(Enum):
    STRUCTURE = "STR"
    RECORD = "REC"
    REFERENCE = "REF"
    FORMAT = "FMT"

    @classmethod
    def values(cls) -> list[str]:
        """Return a list of all rule group values."""
        return [group.value for group in cls]

    @classmethod
    def to_group(cls, id: RuleID) -> RuleGroup | None:
        """Convert a rule ID to a rule group.

        Args:
            id (RuleID): The ID of the rule.

        Returns:
            The rule group if the rule ID belongs to any rule group, otherwise None.
        """
        for g in RuleGroup:
            if g.value in id:
                return g
        return None


class CheckerRegistry(dict[RuleGroup, dict[RuleID, type[Checker]]]):
    def register(self, id: RuleID) -> Callable:
        """Register a checker class.

        Args:
            id (RuleID): The ID of the rule.

        Returns:
            A decorator function that registers the checker class.
        """
        group = RuleGroup.to_group(id)

        if group is None:
            raise ValueError(f"'{id}' doesn't belong to any rule groups: {RuleGroup.values()}")

        def _register_decorator(module: type[Checker]) -> type[Checker]:
            self._add_module(module, group, id)
            return module

        return _register_decorator

    def _add_module(self, module: type[Checker], group: RuleGroup, id: RuleID) -> None:
        if not inspect.isclass(module):
            raise TypeError(f"module must be a class, but got {type(module)}.")

        if group not in self:
            self[group] = {}

        if id in self[group]:
            raise ValueError(f"'{id}' has already been registered.")

        self[group][id] = module

    def build(self, excludes: Sequence[str] | None = None) -> list[Checker]:
        """Build a list of checkers from the registry.

        Args:
            excludes (Sequence[str] | None, optional): A list of rule IDs or rule groups to exclude.

        Returns:
            A list of checkers.
        """
        if excludes is None:
            excludes = []

        return [
            checker(id)
            for group, values in self.items()
            for id, checker in values.items()
            if id not in excludes and group.value not in excludes
        ]


CHECKERS = CheckerRegistry()
