from typing import Callable, Type, Optional as Maybe, Union as U, Union as U
from dataclasses import dataclass, field

class Status:
    ...

from . import engine, observer, unit, scene as scn, target as tgt


EventHandler = tuple[str, int, Callable[[engine.Engine], None]]


def ev(type: str = "", priority: int = 0):
    def decor(body: Callable[[engine.Engine], None]):
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


class Status(metaclass=StatusMeta):
    def __init__(self):
        self._disable: int = 0

        self.parent: Status = None
        self.owner: unit.Unit = None
        self.turns: U[int, None] = None
        self.uses: U[int, None] = None
        self.unbreakable: bool = False
        self.permanent: bool = False
        self.key: bool = False
        self.invisible: bool = False
        self.implicit: bool = False

    def set_relationship(self, target: unit.Unit, owner: unit.Unit):
        self.owner = owner
        owner.inflictors[self] = target

    def enabled(self) -> bool:
        return self._disable == 0

    def enable(self):
        self._disable -= 1

    def disable(self):
        self._disable += 1

    def is_invisible(self) -> bool:
        return self.invisible or self.implicit

    def tick(self) -> bool:
        return False

    def use(self) -> Maybe[Status]:
        return None

    def on_init(self, owner: unit.Unit, scene: scn.Scene, cond: Callable[[engine.Engine], bool] = None):
        for type_, priority, body in getattr(self.__class__, "events", []):
            scene.events[type_].append(observer.Observer(self, owner, body, priority, cond))

    def on_remove(self, scene: scn.Scene):
        for type_, priority, body in getattr(self.__class__, "events", []):
            scene.events[type_] = \
                [*filter(lambda obs: obs.status is self, self.events[type_])]

    def t(self, t) -> Status:
        self.turns = t
        return self

    def u(self, u) -> Status:
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
    def vs(self, cond: Callable[[engine.Engine], bool]) -> Status: pass


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

    def __str__(self) -> str:
        return f"<{self.mount}> {super().__str__()}"
