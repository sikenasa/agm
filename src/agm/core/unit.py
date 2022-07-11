from dataclasses import dataclass, field
from typing import Union as U, Optional as Opt
from enum import Flag, auto

class Unit:
    ...

from . import team, roll, status as status_, action, scene

class UnitEnum(Flag):
    STAY = auto()
    DEAD = auto()
    REMOVED = auto()
    DEF = 0


@dataclass
class Unit:
    name: str
    team: str
    statuses: list[status_.Status] = field(default_factory=list)
    inflictors: dict[status_.Status, Unit] = field(default_factory=dict)
    num_acts: U[int, None] = None
    hp: int = 1
    guard: int = 0
    charge: int = 0
    priority: int = 0

    roles: list[str] = field(default_factory=list)
    max_hp: int = 1
    ap: U[None, roll.Roll, int] = None
    gp: U[None, roll.Roll, int] = None
    cp: U[None, roll.Roll, int] = None
    actions: list[action.Action] = field(default_factory=list)

    flags: UnitEnum = UnitEnum.DEF

    def __eq__(self, o: Unit) -> bool:
        return self is o

    def can_act(self) -> bool:
        return UnitEnum.DEAD | UnitEnum.REMOVED not in self.flags \
            and isinstance(self.num_acts, int) and self.num_acts > 0

    def _link_status(self,
        status: status_.Status,
        scene: scene.Scene,
        target: Unit,
    ) -> None:
        status.on_init(target, scene)
        self.inflictors[status] = target
        status.owner = self
        status.flags &= ~status_.StatusEnum.REMOVED

    def __str__(self):
        return self.show()

    def show(self, status = True, spells = lambda spl: spl.cd > 0) -> str:
        out = self._show_name()

        out += f" HP ｢{self.hp}/{self.max_hp}｣"
        out += self._show_potentials()

        if status:
            out += self._show_statuses()

        if spells:
            out += self._show_actions(spells)
        return out

    def _show_name(self) -> str:
        ret = self.name
        if self.roles:
            ret += f" [{','.join(self.roles)}]"
        return ret

    def _show_potentials(self) -> str:
        ret = ""

        if self.charge is not None and self.charge != 0:
            ret += f" C{'+' if self.charge >= 0 else ''}{self.charge}"
        if self.guard is not None and self.guard != 0:
            ret += f" G{'+' if self.guard >= 0 else ''}{self.guard}"

        return ret

    def _show_statuses(self) -> str:
        sts = [*filter(lambda sts: status_.StatusEnum.INVISIBLE not in sts.flags, self.statuses)]

        if not sts:
            return ""

        return "\n:: " + ", ".join(map(str, sts))

    def _show_actions(self, filter_) -> str:
        if filter_ is False:
            return ""

        if filter_ is True:
            actions = self.actions
        else:
            actions = list(filter(filter_, self.actions))

        if not actions:
            return ""

        return "\n | " + "\n | ".join(map(action.Action.show, actions))
