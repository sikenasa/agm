from dataclasses import dataclass, field
from collections import defaultdict

class Scene:
    ...

from . import unit, team, observer

@dataclass
class Scene:
    units: list[unit.Unit] = field(default_factory=list)
    teams: dict[str, team.Team] = field(default_factory=dict)
    events: dict[str, list[observer.Observer]] = field(default_factory=lambda: defaultdict(list))
    turn: int = 0

    def __post_init__(self):
        self.teams["ally"] = team.Team("ally", "allies")
        self.teams["enemy"] = team.Team("enemy", "enemies")

    def link(self, unit: unit.Unit):
        self.units.append(unit)
        unit.link(self)

    def unlink(self, unit: unit.Unit):
        unit.unlink(self)
        self.units.remove(unit)

    def show(self, status = True, spells = False) -> str:
        ret = f"TURN {self.turn}"

        cur_team = None
        for unit in self.units:
            if unit.team is not cur_team:
                ret += "\n\n"
                cur_team = unit.team
                ret += str(self.teams[cur_team])

            ret += "\n\n"
            ret += unit.show()

        return ret
