from agm.core import ActionType, Engine, Context

Attack = ActionType("Attack", "Deal [AP] damage to a target.")
@Attack.with_body
def _(ctx: Context, eng: Engine):
    pass

Defend = ActionType("Defend", "Grant Guard [GP] to the user.")
@Defend.with_body
def _(ctx: Context, eng: Engine):
    pass

Concentrate = ActionType("Concentrate", "Gain +[CP] Charge to the user.")
@Concentrate.with_body
def _(ctx: Context, eng: Engine):
    pass
