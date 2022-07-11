from dataclasses import dataclass

class Target:
    ...

class Or:
    ...

class And:
    ...

class Not:
    ...

from . import unit as unit, team

class Target:
    def belongs(self, target: unit.Unit) -> bool:
        return True

    def __and__(self, o: Target) -> Target:
        return And(self, o)

    def __or__(self, o: Target) -> Target:
        return Or(self, o)

    def __str__(self) -> str:
        return "Any"

    def __invert__(self) -> Target:
        return Not(self)

Any = Target

@dataclass
class Team(Target):
    _target: team.Team

    def belongs(self, target: unit.Unit) -> bool:
        return target.team is self._target.singular

    def __str__(self) -> str:
        return f"All {self._target.plural}"

@dataclass
class Unit(Target):
    _target: unit.Unit

    def belongs(self, target: unit.Unit) -> bool:
        return target is self._target

    def __str__(self) -> str:
        return f"{self.target.name}"

class And(Target):
    def __init__(self, *targets: list[Target]):
        self._targets = targets

    def belongs(self, target: unit.Unit) -> bool:
        return all(map(t.belongs, self._targets))

    def __and__(self, target: Target) -> Target:
        self._targets.append(target)
        return self

    def __str__(self) -> str:
        return ' && '.join(map(str, self._targets))

class Or(Target):
    def __init__(self, *targets: list[Target]):
        self.targets = targets

    def belongs(self, target: unit.Unit) -> bool:
        return any(t.belongs(target) for t in self.targets)

    def __or__(self, target: Target) -> Target:
        self.targets.append(target)
        return self

    def __str__(self) -> str:
        return " || ".join(map(str, self._targets))

class Not(Target):
    _target: Target

    def belongs(self, target: unit.Unit) -> bool:
        return not self._target.belongs(target)

    def __str__(self) -> str:
        return f"not {self._target}"
