from dataclasses import dataclass

class Target:
    ...

class Or:
    ...

class And:
    ...

from . import unit as unit, team, scene

class Target:
    def belongs(self, target: unit.Unit) -> bool:
        return True

    def __and__(self, o: Target) -> Target:
        return And(self, o)

    def __or__(self, o: Target) -> Target:
        return Or(self, o)

    def show(self) -> str:
        return "Any"

    def __str__(self) -> str:
        return self.show()


@dataclass
class Team(Target):
    target: team.Team

    def belongs(self, target: unit.Unit) -> bool:
        return target.team is self.target.singular

    def show(self) -> str:
        return f"All {self.target.plural}"

@dataclass
class Unit(Target):
    target: unit.Unit

    def belongs(self, target: unit.Unit) -> bool:
        return target is self.target

    def show(self) -> str:
        return f"{self.target.name}"

class And(Target):
    def __init__(self, *targets: list[Target]):
        self.targets = targets

    def __and__(self, target: Target):
        self.targets.append(target)
        return self

    def belongs(self, target: unit.Unit) -> bool:
        return all(t.belongs(target) for t in self.targets)

class Or(Target):
    def __init__(self, *targets: list[Target]):
        self.targets = targets

    def __or__(self, target: Target):
        self.targets.append(target)
        return self

    def belongs(self, target: unit.Unit) -> bool:
        return any(t.belongs(target) for t in self.targets)
