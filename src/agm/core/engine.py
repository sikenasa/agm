from dataclasses import dataclass, field
from functools import wraps
from typing import Union as U

class Engine:
    ...

from . import status, unit
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
    scene: Scene = None
    _top: dict[str, object] = field(default_factory=dict)
    _stack: list[dict[str,object]] = field(default_factory=list)

    def __post_init__(self):
        if self.scene is None:
            self.scene = Scene()

    def __getitem__(self, key) -> object:
        return self._top[key]

    def __setitem__(self, key, value):
        self._top[key] = value

    @property
    def actor(self) -> unit.Unit:
        return self._top["actor"]

    @property
    def action(self) -> Action:
        return self._top["action"]

    @property
    def target(self) -> unit.Unit:
        return self._top["target"]

    @property
    def status(self) -> status.Status:
        return self._top["status"]

    @property
    def source(self) -> unit.Unit:
        return self._top["source"]

    def stop_effect(self):
        raise EffectInterrupt

    def notify(self, type: str):
        for obs in self.scene.events.get(type, []):
            self["status"] = obs.status
            self["source"] = obs.owner

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

    @scoped("actor", "action", "target")
    def attack(self: Engine, damage: U[int, Roll]):
        self._top |= {
            "damage": damage,
            "flat_in": -self.target.guard,
            "flat_out": 0,
            "prop_in": 1.,
            "prop_out": 1.,
        }

        self.notify("out_attack")
        self.notify("in_attack")

        if self.target.dead:
            return

        damage = self["damage"] = int(
            max(0,
                max(0,
                    self["damage"] + self["flat_out"]
                ) * self["prop_out"] + self["flat_in"]
            ) * self["prop_in"]
        )

        self.target.hp = max(0, self.target.hp - damage)

        self.notify("post_attack")

        if self.target.hp > 0:
            return

        self.target.dead = True
        self.notify("death")

        if self.target.stay:
            return

        self.scene.unlink(self.target)
