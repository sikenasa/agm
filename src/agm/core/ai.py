from typing import Callable, Optional
from abc import ABC, abstractmethod

from . import engine, target

class AI(ABC):
    @abstractmethod
    def select_option(self,
        eng: engine.Engine,
        title: str,
        options: list[str],
        times: int = 1,
        tag: Optional[str] = None,
    ) -> list[int]:
        ...
