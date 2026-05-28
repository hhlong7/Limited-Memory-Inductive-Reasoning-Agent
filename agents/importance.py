from facts import Fact
from logic import LogicMemory
from agents.base import BaseAgent


def _shares_argument(a: Fact, b: Fact) -> bool:
    return a.predicate == b.predicate and bool(set(a.args) & set(b.args))

class ImportanceLogic(LogicMemory):
    # Incriment score for reseen fact
    def add_fact(self, fact: Fact) -> None:
        if self.has_fact(fact):
            self.facts[fact]["score"] += 1.0
            return
        
        # Remove the least important fact if fact limit reached
        if len(self.facts) >= self.fact_limit:
            get_rid = min(self.facts.items(), key=lambda item: item[1]["score"])[0]
            del self.facts[get_rid]

        # New fact
        self.facts[fact] = {"score": 1.0}

        for stored_fact in self.facts:
            if stored_fact != fact and _shares_argument(stored_fact, fact):
                self.facts[stored_fact]["score"] += 1.0
    
class ImportanceAgent(BaseAgent):
    # Bot keeps facts based on importance score (times seen)
    def __init__(self, fact_limit: int = 20):
        self.memory = ImportanceLogic(fact_limit=fact_limit, rule_limit=0)

    def process(self, fact: Fact) -> None:
        self.memory.add_fact(fact)

    def answer(self, query: Fact) -> str:
        return self.memory.ask(query)

    def show(self) -> None:
        self.memory.show_facts()
