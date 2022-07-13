from dataclasses import dataclass, field
from collections import defaultdict

class Scene:
    ...

from . import unit, team, observer, target as tgt, engine, status as sts

@dataclass
class Scene:
    units: list[unit.Unit] = field(default_factory=list)
    teams: dict[str, team.Team] = field(default_factory=dict)
    events: dict[str, list[observer.Observer]] = field(default_factory=lambda: defaultdict(list))
    turn: int = 0

    def __post_init__(self):
        self.teams["ally"] = team.Team("ally", "allies")
        self.teams["enemy"] = team.Team("enemy", "enemies")

    def link_unit(self, target: unit.Unit):
        for status in target.statuses:
            target._link_status(status, self, target)
        self.units.append(target)
        target.flags &= ~unit.UnitEnum.REMOVED

    def unlink_unit(self, target: unit.Unit):
        for status in target.statuses:
            owner = status.owner
            self._unlink_status_aux(
                status,
                owner,
                target,
            )

        if len(self.units) > 1:
            idx = self.units.index(target)
            self.units[idx-1].inflictors |= target.inflictors

        target.inflictors.clear()
        self.units.remove(target)
        target.flags |= unit.UnitEnum.REMOVED

    def link_status(self,
        status: sts.Status,
        source: unit.Unit,
        target: unit.Unit = None
    ):
        if target is None:
            target = self

        source._link_status(status, self, target)
        target.statuses.append(status)

    def unlink_status(self, status: sts.Status):
        owner = status.owner
        target = owner.inflictors[status]
        self._unlink_status_aux(status, owner, target)
        target.statuses.remove(status)

    def _unlink_status_aux(self, status: sts.Status, owner, target):
        status.on_remove(self)
        del owner.inflictors[status]
        status.owner = None
        status.flags |= sts.StatusEnum.REMOVED

    def query(self, target: tgt.Target = None):
        if target is None:
            target = tgt.All

        yield from filter(
            lambda u: unit.UnitEnum.REMOVED not in u.flags,
            target.query(self),
        )

    def T(self, team_name: str) -> tgt.Team:
        return tgt.Team(self.teams[team_name])

    def U(self, unit_idx: int) -> tgt.Unit:
        return tgt.Unit(self.units[unit_idx])

    def notify(self, e: engine.Engine, type: str):
        if type not in self.events:
            return

        for obs in [*self.events[type]]:
            if sts.StatusEnum.REMOVED in obs.status.flags:
                continue

            e.ctx.status = obs.status

            if isinstance(obs.owner, unit.Unit):
                obs.callback(e, obs.owner)

            elif isinstance(obs.owner, tgt.Target):
                for unit_ in self.query(obs.owner):
                    obs.callback(e, unit_)

    def get_next_unit_turn(self) -> unit.Unit:
        target: unit.Unit = None

        for u in self.units:
            if u.can_act() and (
                target is None or target.priority < u.priority
            ):
                target = u

        return target

    def __str__(self) -> str:
        return self.show()

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
