from facts import Fact
from logic import LogicMemory
from agents.base import BaseAgent


class SimpleAgent(BaseAgent):
    """Keeps the N most-recent facts, no rule generation. FIFO eviction."""

    def __init__(self, fact_limit: int = 20):
        self.memory = LogicMemory(fact_limit=fact_limit, rule_limit=0)

    def process_fact(self, fact: Fact) -> None:
        self.memory.add_fact(fact)

    def answer_query(self, query: Fact) -> str:
        return self.memory.ask(query)

    def show(self) -> None:
        self.memory.show_facts()
