from typing import Callable, Type, Optional as Maybe
from dataclasses import dataclass, field

class Status:
    ...

from . import engine, observer


EventHandler = tuple[str, int, Callable[[engine.Engine], None]]


def ev(type: Maybe[str] = None, priority: int = 0):
    def decor(body: Callable[[engine.Engine], None]):
        type_ = type if type is not None else body.__name__
        return type_, priority, body
    return decor


class StatusMeta(type):
    def __new__(mcs, name, bases, class_dict):
        class_dict["name"] = class_dict.get("name", name)

        class_dict["events"] = []

        class_obj = super().__new__(mcs, name, bases, class_dict)

        for name, attr in class_obj.__dict__.items():
            if isinstance(attr, tuple):
                class_obj.events.append(attr)

        return class_obj

class Status: ...

class Status(metaclass=StatusMeta):
    def __init__(self):
        self._disable = 0

        self.parent = None
        self.owner = None
        self.turns = None
        self.uses = None
        self.unbreakable = False
        self.permanent = False
        self.key = False
        self.invisible = False
        self.implicit = False

    def enabled(self):
        return self._disable == 0

    def enable(self):
        self._disable -= 1

    def disable(self):
        self._disable += 1

    def show(self) -> str:
        return self.__class__.name

    def tick(self) -> bool:
        return

    def use(self) -> bool:
        pass

    def on_init(self, owner, scene, cond = None):
        for type_, priority, body in self.__class__.events:
            scene.events[type_].append(observer.Observer(self, owner, body, priority, cond))

    def on_remove(self):
        for ev in self.__class__.events:
            print("erase...")

    def t(self, t) -> Status:
        self.turns = t
        return self

    def u(self, u) -> Status:
        self.uses = u
        return self

    def show(self) -> str:
        return f"{self.__class__.name}{self._show_duration()}"

    def _show_duration(self) -> str:
        if self.turns is not None and self.uses is not None:
            return f" ({self.turns}t,{self.uses}u)"

        if self.turns is not None:
            return f" ({self.turns}t)"

        if self.uses is not None:
            return f" ({self.uses}u)"

        return ""


class PotencyStatus(Status):
    def __init__(self, potency: object):
        super().__init__()
        self.potency = potency

    def show(self) -> str:
        return f"{self.__class__.name} [{self.potency}]{self._show_duration()}"
