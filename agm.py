from __future__ import annotations
from enum import Enum, auto
from typing import Callable, OrderedDict
from attr import field
from attrs import define
from copy import deepcopy
from math import ceil
from random import randint

#
# utils
#


def to_clipboard(text):
    from subprocess import Popen, PIPE

    p = Popen(["xclip", "-in", "-selection", "clipboard"], stdin=PIPE)
    p.communicate(input=bytes(text, "utf8"))


#
#
#


@define
class FormatType:
    spells_per_line: int = 2


SCENE_FMT = FormatType()


def select_option(prompt: str, options: list[str], callback: Callable[[int], None]):
    print(prompt)
    for idx, opt in enumerate(options, 1):
        print(f"{idx}: {opt}")

    i = int(input("> ")) - 1

    callback(i)


@define
class Showable:
    def fmt(self, _: list[str]):
        pass

    def show(self) -> str:
        buf = []
        self.fmt(buf)
        return "".join(buf)


@define
class RollableExpr(Showable):
    def roll(self) -> int:
        return 0


@define
class Roll(RollableExpr):
    times: int
    low: int
    high: int

    def roll(self) -> int:
        return sum(randint(self.low, self.high) for _ in range(self.times))


@define
class Spell(Showable):
    name: str
    desc: str
    cd: int | str | None = None
    curr_cd: int | None = 0
    awaits_on_cooldown: bool = False
    visible: bool = True
    dice: list[RollableExpr] = field(factory=list)

    def refresh(self):
        if self.curr_cd is not None and self.curr_cd > 0:
            self.curr_cd -= 1

    def cast(self) -> list[int]:
        self.put_on_cd(self.awaits_on_cooldown)
        return [die.roll() for die in self.dice]

    def put_on_cd(self, wait: bool = False):
        if wait:
            self.curr_cd = None
        elif isinstance(self.cd, int):
            self.curr_cd = self.cd
        else:
            self.curr_cd = None

    def fmt(self, f: list[str]):
        if self.curr_cd is None:
            cd = "W"
        else:
            cd = "R" if self.curr_cd == 0 else self.curr_cd
        f.append(f"{self.name} {cd}/{self.cd}")

    def __str__(self) -> str:
        n = f"{self.name}\n{self.desc}"
        if self.cd is not None:
            n += f"\n{self.cd}"
        return f"```\n{n}\n```"

    __repr__ = __str__


@define
class Gauge:
    curr: int
    max: int

    @classmethod
    def of_max(cls, m: int) -> Gauge:
        return Gauge(m, m)

    def __str__(self) -> str:
        return f"{self.curr}/{self.max}"


@define(kw_only=True)
class Passive(Showable):
    name: str
    desc: str

    def fmt(self, f: list[str]):
        f.append(self.name)
        f.append("\n")
        f.append(self.desc)

    def __str__(self) -> str:
        return self.show()

    __repr__ = __str__


class StatusTickWhen(Enum):
    END_UNIT_TURN = auto()
    START_UNIT_TURN = auto()
    START_TURN = auto()
    END_TURN = auto()


@define
class Status(Showable):
    name: str
    potency: str | int | None = None
    uses: int | None = None
    turns: int | None = None
    permanent: bool = False
    tick_when: StatusTickWhen = StatusTickWhen.END_UNIT_TURN

    def on_scene_turn_start(self, scene: Scene, unit: Unit):
        if self.tick_when == StatusTickWhen.START_TURN:
            self.tick(unit)

    def on_scene_turn_end(self, scene: Scene, unit: Unit):
        if self.tick_when == StatusTickWhen.END_TURN:
            self.tick(unit)

    def on_unit_turn_start(self, scene: Scene, unit: Unit):
        if self.tick_when == StatusTickWhen.START_UNIT_TURN:
            self.tick(unit)

    def on_unit_turn_end(self, scene: Scene, unit: Unit):
        if self.tick_when == StatusTickWhen.END_UNIT_TURN:
            self.tick(unit)

    def tick(self, unit: Unit):
        if self.turns is not None:
            self.turns -= 1
            if self.turns <= 0:
                unit.delete_status(id(self))

    def fmt(self, f: list[str]):
        f.append(self.name)
        if self.potency:
            f.append(f" [{self.potency}]")
        if self.turns is not None or self.uses is not None or self.permanent:
            f.append(" (")
            if self.turns is not None:
                f.append(f"{self.turns}T")
            if self.turns is not None and self.uses is not None:
                f.append(",")
            if self.uses is not None:
                f.append(f"{self.turns}U")
            if (self.uses is not None or self.uses is not None) and self.permanent:
                f.append(" ")
            if self.permanent:
                f.append("P")
            f.append(")")

    def __str__(self) -> str:
        return self.show()

    __repr__ = __str__


@define
class Unit(Showable):
    name: str
    team: str
    role: str
    hp: Gauge

    ap: str
    gp: str
    cp: str

    passives: list[Passive]
    statuses: list[Status]
    spells: list[Spell]

    guard: int = 0
    charge: int = 0

    turn_done: bool = False

    def copy(self) -> Unit:
        return deepcopy(self)

    def fetch_statuses_by_name(self, name: str) -> list[Status]:
        return [status for status in self.statuses if status.name == name]

    def fetch_spell(self) -> Spell:
        o = []

        def f(idx: int):
            o.append(self.spells[idx])

        select_option(
            "Select a spell to fetch",
            [spell.name for spell in self.spells],
            f,
        )

        return o[0]

    def delete_spell(self) -> Spell:
        o = []

        def f(idx: int):
            del self.spells[idx]

        select_option(
            "Select a spell to delete",
            [spell.name for spell in self.spells],
            f,
        )

        return o[0]

    def fetch_status(self) -> Status:
        o = []

        def f(idx: int):
            o.append(self.statuses[idx])

        select_option(
            "Select a status to fetch",
            [status.show() for status in self.statuses],
            f,
        )

        return o[0]

    def _delete_status(self) -> Status:
        o = []

        def f(idx: int):
            del self.statuses[idx]

        select_option(
            "Select a status to delete",
            [status.show() for status in self.statuses],
            f,
        )

        return o[0]

    def delete_status(self, sid: int | None = None):
        if sid is None:
            self._delete_status()

        for idx, status in enumerate(self.statuses):
            if id(status) == sid:
                del self.statuses[idx]
                break

    def deal_damage(
        self,
        src: int,
        flat_atk: int = 0,
        prop_atk: float = 0.0,
        flat_def: int = 0,
        prop_def: float = 0.0,
    ) -> bool:
        prop_atk += 1.0
        prop_def += 1.0
        dmg = round(((src + flat_atk) * prop_atk + flat_def) * prop_def)

        self.hp.curr = max(0, self.hp.curr - dmg)
        print(f"{self.name} takes {dmg} damage", end="")
        if self.hp.curr == 0:
            print(" and dies", end="")
        print("!")
        return self.hp.curr == 0

    def heal_hp(
        self,
        src: int,
        flat_atk: int = 0,
        prop_atk: float = 0.0,
        flat_def: int = 0,
        prop_def: float = 0.0,
    ):
        prop_atk += 1.0
        prop_def += 1.0
        hp = round(((src + flat_atk) * prop_atk + flat_def) * prop_def)
        self.hp.curr = max(self.hp.max, self.hp.curr + hp)
        print(f"{self.name} is healed for {hp}!")

    def start_turn(self, scene: Scene):
        self.guard = 0
        for status in self.statuses:
            status.on_unit_turn_start(scene, self)

    def end_turn(self, scene: Scene):
        idxs = set()
        for status in self.statuses:
            status.on_unit_turn_end(scene, self)
            if status.turns is not None:
                status.turns -= 1
                if status.turns <= 0:
                    idxs.add(id(status))

        self.statuses = [status for status in self.statuses if id(status) not in idxs]

    def fmt(self, f: list[str]):
        f.append(
            f"[{self.role}] {self.name} | HP {self.hp} | G{self.guard:+} C{self.charge:+} | Status: "
        )
        if not self.statuses:
            f.append("N/A")
        else:
            self.statuses[0].fmt(f)
            if len(self.statuses) > 1:
                it = iter(self.statuses)
                next(it, None)
                for status in it:
                    f.append(", ")
                    status.fmt(f)

        spells = [spell for spell in self.spells if spell.visible]
        lines = SCENE_FMT.spells_per_line
        for i in range(ceil(len(spells) / lines)):
            f.append("\n")
            f.append(
                " | ".join(
                    spell.show() for spell in spells[i * lines : (i + 1) * lines]
                )
            )

    def show_stats(self) -> str:
        s = self.show()
        s += f"\nAP {self.ap} GP {self.gp} CP {self.cp}"
        if self.passives:
            s += "\n\nPassives:\n\n" + "\n\n".join(s.show() for s in self.passives)
        return s

    def __str__(self) -> str:
        return self.show_stats()

    __repr__ = __str__


@define(kw_only=True)
class Team(Showable):
    name: str
    units: list[Unit] = field(factory=list)

    def fmt(self, f: list[str]):
        f.append(f">> {self.name} <<")
        for u in self.units:
            f.append("\n\n")
            u.fmt(f)


@define(kw_only=True)
class Scene(Showable):
    turn: int
    teams: OrderedDict[str, Team]
    prev_unit: Unit | None = None

    FMT = SCENE_FMT

    @classmethod
    def new(cls, allies_name: str = "Allies", enemies_name: str = "Enemies") -> Scene:
        o = OrderedDict()
        o["allies"] = Team(name=allies_name, units=[])
        o["enemies"] = Team(name=enemies_name, units=[])
        return cls(
            turn=1,
            teams=o,
        )

    @property
    def allies(self) -> Team:
        return self.teams["allies"]

    @property
    def enemies(self) -> Team:
        return self.teams["enemies"]

    def register_unit(self, unit: Unit) -> Unit:
        self.teams[unit.team].units.append(unit)
        return unit

    def unregister_unit(self, uid: int):
        for team in self.teams.values():
            for i, u in enumerate(team.units):
                if id(u) == uid:
                    del team.units[i]
                    return

    def delete_unit(self):
        def f(idx: int):
            for team in self.teams.values():
                for i, _ in enumerate(team.units):
                    if idx == 0:
                        del team.units[i]
                        return
                    idx -= 1

        select_option(
            "Select an unit to delete",
            [unit.name for team in self.teams.values() for unit in team.units],
            f,
        )

    def fetch_unit(self) -> Unit:
        o = []

        def f(idx: int):
            for team in self.teams.values():
                for i, _ in enumerate(team.units):
                    if idx == 0:
                        o.append(team.units[i])
                        return
                    idx -= 1

        select_option(
            "Select an unit to fetch",
            [unit.name for team in self.teams.values() for unit in team.units],
            f,
        )

        return o[0]

    def fetch_unit_by_name(self, name: str) -> Unit:
        for team in self.teams.values():
            for unit in team.units:
                if unit.name == name:
                    return unit

        assert False and "There should be a name here bro..."

    def fmt(self, f: list[str]):
        f.append(f"Turn {self.turn}")
        for team in self.teams.values():
            f.append("\n\n")
            team.fmt(f)

    def next_unit(self):
        if self.prev_unit:
            self.prev_unit.end_turn(self)

        lst = [unit for team in self.teams.values() for unit in team.units if not unit.turn_done]

        if not lst:
            self.next_turn()
            if any(bool(o.units) for o in self.teams.values()):
                self.next_unit()
        else:
            def f(idx: int):
                unit = lst[idx]
                self.prev_unit = unit
                print(f">> {unit.name}'s turn! <<")
                unit.turn_done = True
                unit.start_turn(self)

            select_option(
                "Select an unit to fetch",
                [unit.name for unit in lst],
                f,
            )

    def next_turn(self):
        if self.prev_unit:
            self.prev_unit.end_turn(self)
            self.prev_unit = None

        self.turn += 1
        print(f">> Next turn! <<")
        for team in self.teams.values():
            for unit in team.units:
                unit.turn_done = False
                for spell in unit.spells:
                    spell.refresh()

    def copy(self) -> Scene:
        return deepcopy(self)

    def manual_write(self, path: str) -> Scene:
        import json
        from yasoo import serialize, deserialize

        with open(path, "w") as f:
            json.dump(serialize(self), f, indent=2)

        input("Please enter to continue...")

        with open(path, "r") as f:
            data = json.load(f)

        return deserialize(data, obj_type=Scene)  # type: ignore

    def __str__(self) -> str:
        return f"```\n{self.show()}\n```"

    __repr__ = __str__


#
# stdlib
#


class PotencyStatus(Status):
    potency: int = 0
    power: int = 0

    def fmt(self, f: list[str]):
        if self.power != 0:
            f.append(f"Power [{self.power}]")
        super().fmt(f)


class DoT(PotencyStatus):
    def on_unit_turn_end(self, scene: Scene, unit: Unit):
        unit.deal_damage(self.potency)
        super().on_unit_turn_end(scene, unit)
