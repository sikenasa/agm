from typing import Union as U, Callable
from ...core import *

class Link(Status):
    def __init__(self, *statuses: list[Status]):
        super().__init__()
        self.statuses = list(statuses)

    def __and__(self, status: Status):
        self.statuses.append(status)
        return self

    def show(self) -> str:
        return " && ".join( map(str, self.statuses))

    def on_init(self, owner: Unit, scene: Engine, cond = None):
        for sts in self.statuses:
            sts.on_init(owner, scene, cond)

    def on_remove(self):
        for sts in self.statuses:
            sts.on_remove(owner)

def _and_(self: Status, o: Status):
    return Link(self, o)

# *tiktok voice* I love open classes!
setattr(Status, "__and__", _and_)

class Aura(MountedStatus):
    def on_init(self, owner: Unit, scene: Scene, cond = None):
        self.mount.on_init(self.potency, scene, cond)

    def on_remove(self, scene: Scene):
        self.mount.on_remove(scene)

def _(self, target: Target) -> Status:
    return Aura(self, target)

# *tiktok voice* I love open classes!
setattr(Status, "aura", _)

class Vs(Status):
    def __init__(self, status: Status, cond: Callable[[Engine], bool]):
        super().__init__()
        self.status = status
        self.cond = cond

        if name in self.data:
            return self.data[name]
        else:
            return 0

    def show(self) -> str:
        return f"{self.status.show()} vs {self.cond}"

    def on_init(self, owner: Unit, scene: Engine, cond = None):
        self.status.on_init(owner, scene, self.cond)

def _(self, target: Callable[[Engine], bool]) -> Status:
    return Vs(self, target)

setattr(Status, "vs", _)
