from agm import *

eng, ctx, scn = Engine.make()

print(sum(len(b) for _,b in scn.events.items()))

for i in range(1, 4):
    scn.link(Unit(f"Sandra#{i}", "ally",
        hp = 90, max_hp = 90,
        statuses = [
            AtkUp(5).aura(scn.T("ally")).u(4),
        ],
    ))

print(sum(len(b) for _,b in scn.events.items()))

while scn.units:
    scn.unlink(scn.units[0])

print(sum(len(b) for _,b in scn.events.items()))

print(scn)
