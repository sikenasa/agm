from abc import ABC, abstractmethod

from . import engine

class AI(ABC):
    @abstractmethod
    def select_option(
        self,
        ctx: engine.Context,
        title: str,
        options: list[str],
    ):
        ...

    @abstractmethod
    def select_target(
        self,
    ):
        ...
