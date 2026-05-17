from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass(frozen=True)
class Fact:
    predicate: str
    # TODO: args are plain strings — no distinction between variables and constants.
    # When FOLCompressionAgent is implemented, consider a Term = Variable | Constant type
    # so generalized rules can be expressed as greater(X, Y) rather than greater("x", "y").
    args: Tuple[str, ...]

    def __str__(self):
        return f"{self.predicate}({', '.join(self.args)})"


@dataclass(frozen=True)
class Rule:
    premises: Tuple[Fact, ...]
    conclusion: Fact
    name: Optional[str] = None
    # TODO: no quantifier information — Rule doesn't record which args are universally
    # quantified variables vs. constants that must match exactly. Needed for proper FOL generalization.

    def __str__(self):
        left = " AND ".join(str(p) for p in self.premises)
        return f"{left} -> {self.conclusion}"
