from dataclasses import dataclass, field
from typing import Union as U, Optional as Opt

class Unit:
    ...

from . import team, roll, status, action, scene

@dataclass
class Unit:
    name: str
    team: str
    actions: list[action.Action] = field(default_factory=list)
    statuses: list[status.Status] = field(default_factory=list)
    inflictors: dict[Unit, status.Status] = field(default_factory=dict)

    roles: list[str] = field(default_factory=list)
    hp: int = 0
    max_hp: int = 1
    num_acts: Opt[int] = None
    ap: U[None, roll.Roll, int] = None
    gp: U[None, roll.Roll, int] = None
    cp: U[None, roll.Roll, int] = None
    guard: int = 0
    charge: int = 0
    priority: int = 0

    stay: bool = False
    dead: bool = False

    def can_act(self) -> bool:
        return not self.dead and isinstance(self.num_acts, int) and self.num_acts > 0

    def link(self, scene: scene.Scene):
        for status in self.statuses:
            status.on_init(self, scene)

    def unlink(self, scene: scene.Scene):
        for status in self.statuses:
            status.on_remove(scene)

    def link_status(self, status: status.Status, scene: scene.Scene):
        self.inflictors[status] = self
        self.statuses.append(status)
        status.on_init(self, scene)

    def unlink_status(self, status: status.Status, scene: scene.Scene):
        status.on_remove(scene)
        del self.inflictors[status]
        self.statuses.remove(status)

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
        sts = [*filter(lambda sts: not sts.invisible, self.statuses)]

        if not sts:
            return ""

        return "\n:: " + ", ".join(map(lambda sts: sts.show(), sts))

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
