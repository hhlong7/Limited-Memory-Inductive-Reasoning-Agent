from abc import ABC, abstractmethod
from facts import Fact


class BaseAgent(ABC):
    @abstractmethod
    def process_fact(self, fact: Fact) -> None:
        pass

    @abstractmethod
    def answer_query(self, query: Fact) -> str:
        pass
