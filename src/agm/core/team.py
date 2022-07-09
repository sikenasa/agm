from dataclasses import dataclass

@dataclass
class Team:
    singular: str
    plural: str

    def __str__(self):
        return f"» {self.plural.title()}' Team «"
