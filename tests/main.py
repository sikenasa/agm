from agm import *

class AtkUp(PotencyStatus):
    @ev()
    def out_attack(c: Engine):
        if c.source is not c.target:
            return

        c["flat_out"] += c.status.potency

ctx = Engine()
scene = ctx.scene

scene.link(Unit(
    "Fairy", "ally",
    hp = 30, max_hp = 30,
    statuses = [AtkUp(5).t(3)],
    ap = 5,
))

scene.link(Unit(
    "Fairy", "enemy",
    hp = 30, max_hp = 30,
    statuses = [AtkUp(5).t(3)],
    ap = 5,
))

ctx["actor"] = scene.units[0]
ctx.perform(Attack())

print(scene.show())
