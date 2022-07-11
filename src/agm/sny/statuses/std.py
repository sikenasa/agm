from ...core import *
from . import builtins

class AtkUp(PotencyStatus):
    @ev()
    def out_attack(ctx, _):
        if ctx.source is not ctx.actor:
            return True
        if isinstance(ctx.status.potency, int):
            ctx.flat_out += ctx.status.potency
        else:
            ctx.prop_out *= ctx.status.potency

class AtkDown(PotencyStatus):
    @ev()
    def out_attack(ctx, _):
        if ctx.source is not ctx.actor:
            return True
        if isinstance(ctx.status.potency, int):
            ctx.flat_out -= ctx.status.potency
        else:
            ctx.prop_out /= ctx.status.potency

class DefUp(PotencyStatus):
    @ev()
    def in_attack(ctx, _):
        if ctx.source is not ctx.target:
            return True
        if isinstance(ctx.status.potency, int):
            ctx.flat_in -= ctx.status.potency
        else:
            ctx.prop_in /= ctx.status.potency

class DefDown(PotencyStatus):
    @ev()
    def in_attack(ctx, _):
        if ctx.source is not ctx.target:
            return True
        if isinstance(ctx.status.potency, int):
            ctx.flat_in += ctx.status.potency
        else:
            ctx.prop_in *= ctx.status.potency

class HealUp(PotencyStatus):
    @ev()
    def out_heal(ctx, _):
        if ctx.source is not ctx.actor:
            return True
        if isinstance(ctx.status.potency, int):
            ctx.flat_out += ctx.status.potency
        else:
            ctx.prop_out *= ctx.status.potency

class HealDown(PotencyStatus):
    @ev()
    def out_heal(ctx, _):
        if ctx.source is not ctx.actor:
            return True
        if isinstance(ctx.status.potency, int):
            ctx.flat_out -= ctx.status.potency
        else:
            ctx.prop_out /= ctx.status.potency

class RecUp(PotencyStatus):
    @ev()
    def in_heal(ctx, _):
        if ctx.source is not ctx.target:
            return True
        if isinstance(ctx.status.potency, int):
            ctx.flat_in += ctx.status.potency
        else:
            ctx.prop_in *= ctx.status.potency

class RecDown(PotencyStatus):
    @ev()
    def in_heal(ctx, _):
        if ctx.source is not ctx.target:
            return True
        if isinstance(ctx.status.potency, int):
            ctx.flat_in -= ctx.status.potency
        else:
            ctx.prop_in /= ctx.status.potency
