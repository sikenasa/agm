from typing import Union as U
from ...core import *

class Link(Status):
    def __init__(self, *statuses):
        super().__init__()
        self.statuses = list(statuses)

    def show(self) -> str:
        return " && ".join(map(lambda sts: sts.show(), self.statuses))

    def on_init(self, owner: Unit, scene: Engine, cond = None):
        for sts in self.statuses:
            sts.on_init(owner, scene, cond)

    def on_remove(self):
        for sts in self.statuses:
            sts.on_remove(owner)

def _and_(self: U[Status, Link], o: Status):
    if isinstance(self, Link):
        self.statuses.append(o)
        return self
    else:
        return Link(self, o)

# *tiktok voice* I love open classes!
setattr(Status, "__and__", _and_)

class Aura(Status):
    def __init__(self, status: Status, target: Target):
        super().__init__()
        self.status = status
        self.target = target

    def show(self) -> str:
        return f"<{self.status.show()}> Aura [{self.target}]{self._show_duration()}"

    def on_init(self, owner: Unit, scene: Engine, cond = None):
        self.status.on_init(self.target, scene, cond)

    def on_remove(self):
        self.status.on_remove()

# *tiktok voice* I love open classes!
setattr(Status, "aura", lambda self, target: Aura(self, target))

