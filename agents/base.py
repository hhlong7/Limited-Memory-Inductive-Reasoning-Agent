from abc import ABC, abstractmethod
from facts import Fact


class BaseAgent(ABC):
    @abstractmethod
    def process(self, fact: Fact) -> None:
        pass

    @abstractmethod
    def answer(self, query: Fact) -> str:
        pass
