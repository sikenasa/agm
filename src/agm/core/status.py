from typing import Callable, Type, Optional, Union as U, Union as U
from dataclasses import dataclass, field
from enum import Flag, auto


class Status:
    ...

from . import engine

EventHandler = tuple[str, int, Callable[[engine.Engine], None]]
Callback = Callable[[object, engine.Engine], None]

from . import observer, unit, scene as scn, target as tgt

def ev(type: str = "", priority: int = 0):
    def decor(body: Callback) -> EventHandler:
        type_ = type if type else body.__name__
        return type_, priority, body
    return decor


class StatusMeta(type):
    def __new__(mcs, name, bases, class_dict):
        class_dict["name"] = class_dict.get("name", name)
        class_obj = super().__new__(mcs, name, bases, class_dict)

        for name, attr in class_dict.items():
            if isinstance(attr, tuple):
                if getattr(class_obj, "events", None) is None:
                    setattr(class_obj, "events", [])
                class_obj.events.append(attr)

        return class_obj


class StatusEnum(Flag):
    UNBREAKABLE = auto()
    UNDISPELLABLE = auto()
    PERMANENT = auto()
    KEY = auto()

    # AGM-specific status types
    INVISIBLE = auto()
    IMPLICIT = auto()
    REMOVED = auto()

    DEF = 0


@dataclass
class Status(metaclass=StatusMeta):
    parent: Status = None
    owner: unit.Unit = None
    turns: U[int, None] = None
    uses: U[int, None] = None

    _disable: int = 0
    flags: StatusEnum = StatusEnum.DEF

    def __hash__(self) -> int:
        return id(self)

    def enabled(self) -> bool:
        return self._disable == 0

    def enable(self):
        self._disable -= 1

    def disable(self):
        self._disable += 1

    def top_parent(self) -> Status:
        parent = self
        while parent.parent is not None:
            parent = parent.parent
        return parent

    def tick(self) -> bool:
        if isinstance(self.turns, int):
            self.turns -= 1
            return self.turns == 0
        else:
            return False

    def use(self) -> Optional[Status]:
        if self.parent is not None:
            sts = self.parent.use()
            if sts is not None:
                return sts

        if isinstance(self.uses, int):
            if self.uses > 0:
                self.uses -= 1

            if self.uses == 0:
                return self.top_parent()

        return None

    def on_init(
        self,
        owner: unit.Unit,
        scene: scn.Scene,
        cond: Optional[Callback] = None
    ):
        for type, priority, body in getattr(self.__class__, "events", []):
            scene.events[type].append(
                observer.Observer(self, priority, owner, body, cond)
            )

    def on_remove(self, scene: scn.Scene):
        for type, priority, body in getattr(self.__class__, "events", []):
            scene.events[type].remove(observer.Observer(self))

    def t(self, t: U[int]) -> Status:
        self.turns = t
        return self

    def u(self, u: int) -> Status:
        self.uses = u
        return self

    def to_implicit(self) -> Status:
        self.implicit = True
        return self

    def __str__(self) -> str:
        return f"{self.__class__.name}{self._show_duration()}"

    def _show_duration(self) -> str:
        if self.turns is not None and self.uses is not None:
            return f" ({self.turns}t,{self.uses}u)"

        if self.turns is not None:
            return f" ({self.turns}t)"

        if self.uses is not None:
            return f" ({self.uses}u)"

        return ""

    def aura(self, target: tgt.Target) -> Status: pass
    def vs(self, cond: Callback) -> Status: pass


class PotencyStatus(Status):
    def __init__(self, potency: object):
        super().__init__()
        self.potency = potency

    def __str__(self) -> str:
        return f"{self.__class__.name} [{self.potency}]{self._show_duration()}"


class MountedStatus(PotencyStatus):
    def __init__(self, mount: Status, potency: object):
        super().__init__(potency)
        self.mount = mount
        mount.parent = self

    def __str__(self) -> str:
        return f"<{self.mount}> {super().__str__()}"
