from agm.core import ActionType, Engine

Attack = ActionType("Attack", "Deal [AP] damage to a target.")

@Attack.with_body
def _(c: Engine):
    c.target = c.scene.units[-1]
    c.attack(c.roll(c.actor.ap))

Defend = ActionType("Defend", "Grant Guard [GP] to the user.")

@Defend.with_body
def _(c: Engine):
    c.target = c.actor
    c.target.guard += c.roll(c.actor.gp)

Concentrate = ActionType("Concentrate", "Gain +[CP] Charge to the user.")

@Concentrate.with_body
def _(c: Engine):
    c.target = c.actor
    c.target.charge += c.roll(c.actor.cp)
