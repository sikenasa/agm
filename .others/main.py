from agm import *
import random

eng, ctx, scn = Engine.make()

names = [
    "Sandra",
    "Sarah",
    "Oru",
    "Renée",
]
hps = [
    80,
    95,
    70,
    80,
]

for name, hp in zip(names, hps):
    scn.link_unit(Unit(name, "ally",
        hp = hp, max_hp = hp,
        ap = D[11:14],
        gp = D[8:12],
        cp = 5,
        actions = [Attack(), Defend(), Concentrate()],
    ))

eng.global_turn()
