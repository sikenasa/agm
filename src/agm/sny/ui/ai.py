from ...core import ai, Engine

class AI(ai.AI):
    def select_option(self,
        eng: Engine,
        title: str,
        options: list[str],
        times: int = 1,
    ) -> int:
        print(options)
