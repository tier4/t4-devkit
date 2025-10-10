from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from enum import Enum, unique

from .checker import Checker, RuleID


@unique
class RuleGroup(Enum):
    STRUCTURE = "STR"
    SCHEMA = "SCH"
    REFERENCE = "REF"
    FORMAT = "FMT"

    @classmethod
    def values(cls) -> list[str]:
        return [group.value for group in cls]


class CheckerRegistry(dict[RuleGroup, dict[RuleID, type[Checker]]]):
    def register(self, id: RuleID) -> Callable:
        # TODO(ktro2828); Need to validate code after splitting code into group and number
        group = None
        for g in RuleGroup:
            if g.value in id:
                group = g

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
        if excludes is None:
            excludes = []

        return [
            checker(rule)
            for _, values in self.items()
            for rule, checker in values.items()
            if rule not in excludes
        ]


CHECKERS = CheckerRegistry()
