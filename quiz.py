from dataclasses import dataclass
from typing import List, Tuple, Protocol
from facts import Fact


class Agent(Protocol):
    def answer_query(self, query: Fact) -> str: ...


@dataclass
class QuizResult:
    total: int
    correct: int       # answer matched expected
    unknown_count: int # agent said "Unknown"

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0.0

    @property
    def answer_rate(self) -> float:
        answered = self.total - self.unknown_count
        return answered / self.total if self.total > 0 else 0.0

    def __str__(self) -> str:
        answered = self.total - self.unknown_count
        return (
            f"Correct: {self.correct}/{self.total} ({self.accuracy:.1%}) | "
            f"Answered: {answered}/{self.total} ({self.answer_rate:.1%}) | "
            f"Unknown: {self.unknown_count}"
        )


def run_quiz(agent: Agent, questions: List[Tuple[Fact, str]]) -> QuizResult:
    correct = 0
    unknown_count = 0
    for fact, expected in questions:
        answer = agent.answer(fact)
        if answer == "Unknown":
            unknown_count += 1
        if answer == expected:
            correct += 1
    return QuizResult(total=len(questions), correct=correct, unknown_count=unknown_count)
