from agm.core import ActionType, Engine

@ActionType(
    "Attack",
    "Deal [AP] damage to a target.",
).with_
def Attack(c: Engine):
    c["target"] = c.scene.units[-1]
    c.attack(c.roll(c.actor.ap))

@ActionType(
    "Defend",
    "Grant Guard [GP] to the user.",
).with_
def Defend(c: Engine):
    c["target"] = c.actor
    c["target"].guard += c.roll(c.actor.gp)

@ActionType(
    "Concentrate",
    "Gain +[CP] Charge to the user.",
).with_
def Defend(c: Engine):
    c["target"] = c.actor
    c["target"].charge += c.roll(c.actor.cp)
