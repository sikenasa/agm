from dataclasses import dataclass

class Target:
    ...

from . import unit

class Target:
    def belongs(self, unit: unit.Unit) -> bool:
        return True

@dataclass
class Team(Target):
    team: str

    def belongs(self, unit: unit.Unit) -> bool:
        return unit.team == self.team
