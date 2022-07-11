from dataclasses import dataclass, field
from functools import wraps
from typing import Union as U

class Engine: ...
class Context: ...

from .unit import Unit, UnitEnum
from .target import Target
from .status import Status
from .roll import Roll, D
from .action import Action
from .scene import Scene
from . import ai

class ActionInterrupt(Exception): ...
class EffectInterrupt(Exception): ...

class Context:
    def __or__(self, o: dict) -> Context:
        self.__dict__ |= o
        return self

def scoped(*inherit):
    def decorator(f):
        @wraps(f)
        def wrapper(self: Engine, *args, with_ctx = False, **kwargs):
            prev_ctx = self.ctx

            scope = Context() | prev_ctx.__dict__

            self.ctx = scope

            try:
                res = f(self, scope, *args, **kwargs)
            except ActionInterrupt:
                pass

            self.ctx = prev_ctx

            return (res, scope) if with_ctx else res
        return wrapper
    return decorator

@dataclass
class Engine:
    scene: Scene = field(default_factory=Scene)
    ctx: Context = field(default_factory=Context)
    proxy: dict[Unit, ai.AI] = field(default_factory=dict)

    def make() -> (Engine, Context, Scene):
        eng = Engine()
        return eng, eng.ctx, eng.scene

    def stop_effect(self):
        raise EffectInterrupt

    def notify(self, type: str) -> None:
        self.scene.notify(self, type)

    def global_turn(self):
        self.scene.tick_global_turn()
        self.notify("global_tick")

    @scoped("actor")
    def unit_turn(self, ctx):
        actor: Unit = ctx.actor
        self.scene.tick_unit_turn(actor)
        self.notify("pre_unit_turn")

        while actor.num_acts is not None and actor.num_acts > 0:
            actor.num_acts -= 1

        self.notify("post_unit_turn")
        ctx.actor.num_acts = None

    @scoped("actor", "target")
    def perform(self, ctx, action: Action):
        ctx |= { "action": action, "cooldown": action.type.cd }

        self.notify("pre_action")

        action.cd = ctx.cooldown

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
    def roll_generic(self, ctx, dice: Roll, use_charge = False) -> int:
        ctx.dice = dice

        self.notify("pre_roll")

        ret = ctx.dice.roll()
        if use_charge:
            ret += ctx.actor.charge

        self.notify("post_roll")

        return ret

    @scoped("actor", "action")
    def select_target(self,
        ctx: Context,
        type: str,
        target: Target = None,
        num_targets: int = 1,
        aoe: bool = False
    ) -> list[Unit]:
        uts = self.scene.units[-1:]

        ctx |= { "target": uts, "type": type }
        self.notify("target")

        return uts

    @scoped("actor", "action")
    def select_team(self,
        ctx,
        team: str,
        num_targets: int = 1
    ) -> list[Unit]:
        uts = [*filter(u for u in self.scene.units if u.team == team)]

        return uts

    @scoped("actor", "action")
    def attack(self,
        ctx,
        damage: int,
        targets: list[Unit] = None,
        aoe: bool = False
    ):
        ctx |= {
            "out_damage": damage,
            "flat_out": 0,
            "prop_out": 1.,
            "aoe": aoe,
        }

        self.notify("out_attack")

        ctx.out_damage = max(0, ctx.out_damage + ctx.flat_out) * ctx.prop_out

        if targets is None:
            targets = [self.actor]

        for t in targets:
            if UnitEnum.REMOVED in t.flags:
                continue

            ctx |= {
                "damage": ctx.out_damage,
                "target": t,
                "flat_in": -t.guard,
                "prop_in": 1.,
            }
            self.notify("in_attack")

            if UnitEnum.DEAD in t.flags:
                continue

            damage = ctx.damage = int(max(0, ctx.damage + ctx.flat_in) * ctx.prop_in)
            t.hp = max(0, t.hp - damage)
            self.notify("post_attack")

            if t.hp > 0:
                continue

            t.flags |= UnitEnum.DEAD
            self.notify("death")

            if UnitEnum.STAY in t.flags:
                continue

            self.scene.unlink(t)
