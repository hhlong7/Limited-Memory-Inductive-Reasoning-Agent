import random
from facts import Fact
from logic import LogicMemory
from agents.base import BaseAgent

class RandomLogic(LogicMemory):
    #throw away random facts instead of FIFO
    def add_fact(self, fact: Fact) -> None:

        if self.has_fact(fact):
            return #no dups
        
        if len(self.facts) >= self.fact_limit:
            random_fact = random.choice(list(self.facts.keys()))
            del self.facts[random_fact] 
            #random del for when exceed the fact limits

        self.facts[fact] = {"score": 0.0}

class RandomAgent(BaseAgent):
    #ts bot would randomly choose which fact to forget and which to keep: del policy

    def __init__(self, fact_limit: int = 20):
        self.memory = RandomLogic(fact_limit=fact_limit, rule_limit=0)

    def process(self, fact: Fact) -> None:
        self.memory.add_fact(fact) 
        #feeding the bot facts, evicting facts dealt with in add_fact func

    def answer(self, question: Fact) -> str:
        return self.memory.ask(question)
    
    def show(self) -> None:
        self.memory.show_facts()
