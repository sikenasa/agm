from dataclasses import dataclass
from typing import Callable, Union, Optional

class Observer:
    ...

from . import status as sts, engine, unit, target

@dataclass
class Observer:
    status: sts.Status
    priority: int = None
    owner: Union[unit.Unit, target.Target] = None
    body: sts.Callback = None
    cond: Optional[sts.Callback] = None

    def __less__(self, o: Observer) -> bool:
        return self.priority < o.priority

    def __eq__(self, o: Observer) -> bool:
        return self.status is o.status

    def callback(self, e: engine.Engine, unit: unit.Unit) -> None:
        e.ctx.source = unit

        if self.cond is not None and not self.cond(e.ctx, e):
            return None

        if not self.body(e.ctx, e):
            s = self.status.use()
            if s is not None:
                s.flags |= sts.StatusEnum.REMOVED
                e.remove_status(s)
