class Target:
    ...

class Team:
    ...

class Unit:
    ...

class Or:
    ...

class And:
    ...

class Not:
    ...

from . import unit as unit, team, scene
from dataclasses import dataclass, field
from typing import Iterator

class Target:
    def belongs(self, target: unit.Unit) -> bool:
        return True

    def query(self, scn: scene.Scene) -> Iterator[unit.Unit]:
        yield from filter(self.belongs, scn.units)

    def __and__(self, o: Target) -> Target:
        return And(self, o)

    def __or__(self, o: Target) -> Target:
        return Or(self, o)

    def __str__(self) -> str:
        return "Any"

    def __invert__(self) -> Target:
        return Not(self)

All = Target()

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
        return f"{self._target.name}"

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

@dataclass
class Multi(Target):
    def __init__(self, *targets: list[unit.Unit]):
        self._targets = targets

    def belongs(self, tgt: unit.Unit) -> bool:
        return tgt in self._targets

    def query(self, scn: scene.Scene) -> Iterator[unit.Unit]:
        yield from self._targets

    def __str__(self) -> str:
        return ", ".join(map(lambda u: u.name, self._targets))

class Seq(Target):
    def __init__(self, *targets: list[Target]):
        self._targets = targets

    def belongs(self, tgt: unit.Unit) -> bool:
        return any(t.belongs(tgt) for t in self._targets)

    def query(self, scn: scene.Scene) -> Iterator[unit.Unit]:
        for t in self._targets:
            yield from t.query(scn)

    def __str__(self) -> str:
        return ", then ".join(map(str, self._targets))
