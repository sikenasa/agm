from dataclasses import dataclass, field
from functools import wraps
from typing import Union as U

class Engine:
    ...

from .unit import Unit
from .target import Target
from .status import Status
from .roll import Roll, D
from .action import Action
from .scene import Scene

class ActionInterrupt(Exception): ...
class EffectInterrupt(Exception): ...

def scoped(*inherit):
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, with_ctx = False, **kwargs) -> object:
            scope = {}
            for key in inherit:
                scope[key] = self[key]
            self._stack.append(self._top)
            self._top = scope

            try:
                res = f(self, *args, **kwargs)
            except ActionInterrupt:
                pass

            self._top = self._stack.pop()

            if with_ctx:
                return res, scope
            else:
                return res
        return wrapper
    return decorator

@dataclass
class Engine:
    scene: Scene = field(default_factory=Scene)
    _top: dict[str, object] = field(default_factory=dict)
    _stack: list[dict[str,object]] = field(default_factory=list)

    def __getitem__(self, key) -> object:
        return self._top[key]

    def __setitem__(self, key, value):
        self._top[key] = value

    @property
    def actor(self) -> Unit:
        return self._top["actor"]

    @actor.setter
    def actor(self, unit: Unit):
        self._top["actor"] = unit

    @property
    def action(self) -> Action:
        return self._top["action"]

    @action.setter
    def action(self, action: Action):
        self._top["action"] = action

    @property
    def target(self) -> Unit:
        return self._top["target"]

    @target.setter
    def target(self, unit: Unit):
        self._top["target"] = unit

    @property
    def status(self) -> Status:
        return self._top["status"]

    @status.setter
    def status(self, status: Status):
        self._top["status"] = status

    @property
    def source(self) -> Unit:
        return self._top["source"]

    @source.setter
    def source(self, unit: Unit):
        self._top["source"] = unit

    def stop_effect(self):
        raise EffectInterrupt

    def notify(self, type: str):
        for obs in self.scene.events.get(type, []):
            self.status = obs.status

            if isinstance(obs.owner, Unit):
                self.source = obs.owner
                if obs.cond is not None and not obs.cond(self):
                    continue
                obs.body(self)

            elif isinstance(obs.owner, Target):
                for unit in self.scene.query(obs.owner):
                    self.source = unit
                    if obs.cond is not None and not obs.cond(self):
                        continue
                    obs.body(self)

    @scoped("actor")
    def perform(self, action: Action):
        self["action"] = action
        self["cooldown"] = action.max_cd

        self.notify("pre_action")

        action.cd = self["cooldown"]

        self.notify("post_cooldown")

        action.type.body(self)

        self.notify("post_action")

    def roll_chance(self):
        return self.roll_generic(D(100), use_charge = False)

    def roll(self, dice: U[Roll, int], use_charge = True) -> int:
        if isinstance(dice, int):
            return dice

        return self.roll_generic(dice, use_charge = use_charge)

    @scoped("actor")
    def roll_generic(self, dice: Roll, use_charge = False, with_ctx = False) -> int:
        self["dice"] = dice

        self.notify("pre_roll")

        ret = self["dice"].roll()
        if use_charge:
            ret += self.actor.charge

        self.notify("post_roll")

        return ret

    @scoped("actor", "action")
    def select_target(self, type: str, filter_: Target = None, num_targets: int = 1, aoe: bool = False) -> list[Unit]:
        uts = self.scene.units[-1:]

        self._top |= { "target": uts, "type": type }
        self.notify("target")

        return uts

    @scoped("actor", "action")
    def select_team(self, team: str, num_targets: int = 1) -> list[Unit]:
        uts = [*filter(u for u in self.scene.units if u.team == team)]

        return uts

    @scoped("actor", "action")
    def attack(self: Engine, damage: int, targets: list[Unit] = None, aoe: bool = False):

        self._top |= {
            "out_damage": damage,
            "flat_out": 0,
            "prop_out": 1.,
            "aoe": aoe,
        }

        self.notify("out_attack")
        self["out_damage"] = max(0, self["out_damage"] + self["flat_out"]) * self["prop_out"]

        if targets is None:
            targets = [self.actor]

        for t in targets:
            self._top |= {
                "damage": self["out_damage"],
                "target": t,
                "flat_in": -t.guard,
                "prop_in": 1.,
            }
            self.notify("in_attack")

            if t.dead:
                continue

            damage = self["damage"] = int(max(0, self["damage"] + self["flat_in"]) * self["prop_in"])

            t.hp = max(0, t.hp - damage)

            self.notify("post_attack")

            if t.hp > 0:
                continue

            t.dead = True
            self.notify("death")

            if t.stay:
                continue

            self.scene.unlink(t)
