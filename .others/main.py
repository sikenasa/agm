from agm import *

class AtkUp(PotencyStatus):
    @ev()
    def out_attack(ctx: Engine):
        if ctx.source is not ctx.actor:
            return

        ctx["flat_out"] += ctx.status.potency

ctx = Engine()
scn = ctx.scene

for _ in range(2):
    scn.link(Unit(
        "Sandra", "ally",
        hp = 90, max_hp = 90,
        statuses = [AtkUp(5).aura(scn.T("ally")).t(3)]
    ))

for _ in range(3):
    scn.link(Unit(
        "Sandra", "enemy",
        hp = 90, max_hp = 90,
    ))

ctx.actor = scn.units[0]
ctx.action = None
ctx.attack(20, scn.query(scn.T("enemy")))
print(scn.show())
