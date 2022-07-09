from dataclasses import dataclass
from random import randrange
from typing import Iterator, Union as U

class Roll: ...

@dataclass
class Roll:
    min: int = 1
    max: int = 20
    num: int = 1

    def roll_a(self) -> Iterator[int]:
        return (
            randrange(self.min, self.max)
            for _ in range(0, self.num)
        )

    def roll(self) -> int:
        return sum(self.roll_a())

    def __str__(self) -> str:
        if self.num == 1:
            return f"d{self.max}" if self.min == 1 else f"[{self.min}~{self.max}]"
        else:
            return f"{self.num}d{self.max}" if self.min == 1 else f"{self.num}d[{self.min}~{self.max}]"

    def __getitem__(self, range: U[slice, int]) -> Roll:
        if isinstance(range, slice):
            if range.step is not None:
                return Roll(
                    1 if range.stop is None else range.stop,
                    20 if range.step is None else range.step,
                    1 if range.start is None else range.start,
                )
            else:
                return Roll(
                    1 if range.start is None else range.start,
                    20 if range.stop is None else range.stop,
                )
        else:
            return Roll(max=range)

D = Roll(max=100)
