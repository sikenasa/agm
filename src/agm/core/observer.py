from dataclasses import dataclass
from typing import Callable, Union as U

class Observer:
    ...

from . import status, engine, unit, target

@dataclass
class Observer:
    status: status.Status
    owner: U[unit.Unit, target.Target]
    body: Callable[[engine.Engine], None]
    priority: int
    cond: Callable[[engine.Engine], bool]
