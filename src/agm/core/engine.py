
class Engine: ...
class Context: ...

from .unit import Unit, UnitEnum
from .target import Target
from .status import Status
from .roll import Roll, D
from .action import Action
from .scene import Scene
from . import ai, stage

from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Union as U, Optional, Callable
from contextlib import contextmanager, nullcontext

class FightInterrupt(Exception): ...
class WaveInterrupt(Exception): ...
class GlobalTurnInterrupt(Exception): ...
class UnitTurnInterrupt(Exception): ...
class ActionInterrupt(Exception): ...
class EffectInterrupt(Exception): ...
class AtomInterrupt(Exception): ...

Nil = object()

class Context:
    def __init__(self, ctx: dict = None):
        if ctx:
            self.__dict__ = ctx

    def __setitem__(self, k, v):
        self.__dict__[k] = v

    def __getitem__(self, k):
        return self.__dict__.get(k, None)

    def __or__(self, o: dict) -> Context:
        self.__dict__ |= o
        return self

    def __contains__(self, o) -> bool:
        return o in self.__dict__

    def __str__(self) -> str:
        return dict.__str__(self)

    def export(self, vars: dict, *exports: list[str]) -> Context:
        ctx = Context()
        if exports:
            for k in exports:
                ctx[k] = self[k]

        for k,v in vars.items():
            if v is not Nil:
                ctx[k] = v
            else:
                ctx[k] = self[k]
        return ctx

@dataclass
class Engine:
    scene: Scene = field(default_factory=Scene)
    ctx: Context = field(default_factory=Context)
    stg: stage.Stage = field(default_factory=stage.Stage)
    proxy: dict[Unit, ai.AI] = None
    default_proxy: Optional[ai.AI] = None
    stop_callback: Optional[Callable[[Engine], None]] = None

    SPACE_TYPE = {
        "fight": (FightInterrupt, "pre_fight", "post_fight"),
        "wave": (WaveInterrupt, "pre_wave", "post_wave"),
        "global_turn": (GlobalTurnInterrupt, "pre_global_turn", "post_global_turn"),
        "unit_turn": (UnitTurnInterrupt, "pre_unit_turn", "post_unit_turn"),
        "action": (ActionInterrupt, "pre_action", "post_action"),
        "effect": (EffectInterrupt, "pre_effect", "post_effect"),
    }

    def __post_init__(self):
        self.proxy = defaultdict(self.default_proxy)

    #
    # --- Basic Operations ---
    #

    def make() -> (Engine, Context, Scene):
        eng = Engine()
        return eng, eng.ctx, eng.scene

    def notify(self, type: str) -> None:
        self.ctx.notify_type = type

        if self.stop_callback:
            self.stop_callback(self)

        self.scene.notify(self, type)

    def throw(self, type: str = None):
        if type is None:
            type = self.ctx.type

        raise Engine.SPACE_TYPE[type][0]()

    def scope(self,
        type: str,
        *exports: list[str],
        **vars,
    ):
        if type in Engine.SPACE_TYPE:
            return self._scope_timeframe(type, exports, vars)
        else:
            return self._scope_atom(type, exports, vars)

    @contextmanager
    def _scope_timeframe(self: Engine,
        type: str,
        export: list[str],
        vars: dict,
    ):
        prev_ctx = self.ctx

        self.ctx = self.ctx.export(vars, *export)
        self.ctx.type = type

        exc, pre, post = Engine.SPACE_TYPE[type]

        try:
            self.notify(pre)
            yield self.ctx
            self.notify(post)
        except exc:
            pass
        finally:
            self.ctx = prev_ctx

    @contextmanager
    def _scope_atom(self,
        type: str,
        export: list[str],
        vars: dict,
    ):
        prev_ctx = self.ctx

        self.ctx = self.ctx.export(vars, *export)
        self.ctx.type = "atom"
        self.ctx.atom_type = type

        try:
            yield self.ctx
        except AtomInterrupt:
            pass
        finally:
            self.ctx = prev_ctx

    def atom(self, prefix: str, event: str) -> None:
        self.ctx.type = event
        self.notify(f"{prefix}_atom")
        self.notify(f"{prefix}_{event}")

    #
    # --- Global Turn ---
    #

    def global_turn(self):
        self.scene.turn += 1
        for unit in self.scene.units:
            unit.num_acts = 1
            for act in unit.actions:
                act.tick()

        with self.scope("global_turn"):
            while (target := self.scene.get_next_unit_turn()) is not None:
                self.unit_turn(target)

    #
    # --- Unit Turn ---
    #

    def unit_turn(self, actor: Unit):
        self.ctx.actor = actor
        for status in [*actor.inflictors.keys()]:
            if status.tick():
                self.remove_status(status)

        with self.scope("unit_turn", "actor") as ctx:
            while (
                isinstance(ctx.actor.num_acts, int) and
                ctx.actor.num_acts > 0
            ):
                ctx.actor.num_acts -= 1
                self.perform(ctx.actor.actions[0], ctx.actor)

        actor.num_acts = None

    #
    # --- Action Time ---
    #

    def perform(self, action: Action, actor: Unit = None):
        if not action.usable():
            return

        ctx = self.ctx
        ctx.action = action

        if actor is not None:
            ctx.actor = actor

        ctx.cooldown = action.type.cd
        self.notify("pre_cd")
        action.cd = ctx.cooldown

        with self.scope("action",
            "actor", "action", "cooldown",
        ) as ctx:
            action.type.body(ctx, self)

        return ctx

    #
    # --- Other ---
    #

    #
    # Select Target
    #

    def lock_tgt(self,
        times: int = 1,
        sorting = lambda: True,
        tag: str = None,
    ) -> Target:
        with self.scope("target"
            "actor", "action",
            tag = tag,
            times = times,
            available = defaultdict(int),
        ) as ctx:
            self.atom("pre", "target")

            self.proxy[ctx.actor].select_option(
                title = title,
                tag = ctx.tag,
            )

            self.atom("post", "target")

    #
    #   Roll
    #

    def roll_chance(self) -> int:
        return self.roll_generic(D(100), use_charge = False)

    def roll(self, dice: U[Roll, int], use_charge = True) -> int:
        if isinstance(dice, int):
            return dice
        return self.roll_generic(dice, use_charge = use_charge, actor = None)

    def roll_generic(self, dice: Roll, use_charge: U[bool, int] = False, actor: Unit = Nil) -> int:
        with self.scope("roll",
            actor = Nil,
            dice = dice,
            use_charge = use_charge,
        ) as ctx:
            self.notify("pre_roll")

            if isinstance(ctx.use_charge, int):
                added_chg = min(ctx.use_charge, ctx.actor.charge)
            elif ctx.use_charge:
                added_chg = ctx.actor.charge
            else:
                added_chg = 0

            ret = ctx.dice.roll()
            if ctx.actor:
                ret += added_chg
                ctx.actor.charge -= added_chg
            ctx.roll_result = ret

            self.notify("post_roll")
            return ret

# ctx.out_damage = max(0, ctx.out_damage + ctx.flat_out) * ctx.prop_out
# damage = ctx.damage = int(max(0, ctx.damage + ctx.flat_in) * ctx.prop_in)

    #
    #   Status Manip
    #

    def inflict_status(self,
        status: Status,
        target: Unit,
        actor: Unit = Nil,
    ):
        with self.scope("inflict",
            actor = actor,
            status = status,
            target = target,
        ) as ctx:
            if not ctx.actor:
                self.atom("out", "inflict")

            self.atom("in", "inflict")

            if not ctx.actor:
                ctx.actor = ctx.target

            self.scene.link_status(ctx.status, ctx.actor, ctx.target)
            self.atom("hit", "inflict")

    def remove_status(self,
        status: Status,
        actor: Unit = None,
        dispel: bool = False,
        break_: bool = False,
        expire: bool = True,
    ):
        with self.scope("remove_status",
            status = status,
            actor = actor,
            dispel = dispel,
            break_ = break_,
            expire = expire,
        ) as ctx:
            if not ctx.actor:
                self.atom("out", "dispel")

            self.atom("in", "dispel")
            self.scene.unlink_status(ctx.status)
            self.atom("post", "dispel")
