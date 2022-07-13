from typing import Callable, Type, Optional as Maybe
from dataclasses import dataclass, field

class Action:
    ...

class ActionType:
    ...

from . import engine, status

@dataclass
class ActionType:
    name: str
    doc: str
    cd: int = 0
    body: Callable[[engine.Context, engine.Engine], None] = None
    passive: Callable[[], status.Status] = None

    def with_body(self, f):
        self.body = f

    def with_passive(self, f):
        self.passive = f

    def __call__(self):
        return Action(self)

@dataclass
class Action:
    type: ActionType
    cd: int = 0
    _disable: int = 0
    _passive: status.Status = None

    def __post_init__(self):
        self._disable = 0

    def usable(self) -> bool:
        return self.enabled() and self.cd == 0

    def tick(self) -> bool:
        if self.cd > 0:
            self.cd -= 1
        return self.cd == 0

    def enabled(self) -> bool:
        return self._disable == 0

    def disable(self):
        self._disable += 1

    def enable(self):
        self._disable -= 1

    def __str__(self):
        out = self.type.name

        if not (self.cd == 0 and self.max_cd == 0):
            if self.cd is None:
                out += " W"
            elif self.cd == 0:
                out += " R"
            else:
                out += f" {self.cd}"
            out += f"/{self.max_cd}"

        return out
