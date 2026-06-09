from dataclasses import dataclass, field
from typing import List, Tuple, Protocol
from facts import Fact

UnknownEntry = Tuple[Fact, str, str]  # query, expected, answer


class Agent(Protocol):
    def answer_query(self, query: Fact) -> str: ...


@dataclass
class QuizResult:
    total: int
    correct: int       # answer matched expected
    unknown_count: int # agent said "Unknown"
    committed_rules: Tuple[str, ...] = field(default_factory=tuple)
    unknowns: List[UnknownEntry] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0.0

    @property
    def answer_rate(self) -> float:
        answered = self.total - self.unknown_count
        return answered / self.total if self.total > 0 else 0.0

    def __str__(self) -> str:
        answered = self.total - self.unknown_count
        rule_label = ", ".join(self.committed_rules) if self.committed_rules else "none"
        return (
            f"Correct: {self.correct}/{self.total} ({self.accuracy:.1%}) | "
            f"Answered: {answered}/{self.total} ({self.answer_rate:.1%}) | "
            f"Unknown: {self.unknown_count} | "
            f"Rule: {rule_label}"
        )

    def print_unknowns(self) -> None:
        if not self.unknowns:
            print("Unknown questions: none")
            return
        print(f"Unknown questions ({len(self.unknowns)}):")
        for fact, expected, answer in self.unknowns:
            print(f"  {fact} expected {expected} (got {answer})")


def _committed_rule_names(agent: Agent) -> Tuple[str, ...]:
    rules = getattr(agent, "committed_rules", None)
    if not rules:
        return ()
    names = []
    for rule in rules:
        names.append(rule.name if getattr(rule, "name", None) else str(rule))
    return tuple(names)


def run_quiz(
    agent: Agent,
    questions: List[Tuple[Fact, str]],
    show_unknowns: bool = False,
) -> QuizResult:
    correct = 0
    unknown_count = 0
    unknowns: List[UnknownEntry] = []
    for fact, expected in questions:
        answer = agent.answer(fact)
        if answer == "Unknown":
            unknown_count += 1
            unknowns.append((fact, expected, answer))
        if answer == expected:
            correct += 1
    result = QuizResult(
        total=len(questions),
        correct=correct,
        unknown_count=unknown_count,
        committed_rules=_committed_rule_names(agent),
        unknowns=unknowns,
    )
    if show_unknowns:
        result.print_unknowns()
    return result
