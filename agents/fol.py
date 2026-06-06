from facts import Fact, Rule
from logic import LogicMemory, ask_with_grounded_rules
from universal import generate_universe
from agents.base import BaseAgent


class FOLCompressionAgent(BaseAgent):
    def __init__(self, fact_limit: int = 20, rule_limit: int = 20):
        self.memory = LogicMemory(fact_limit=fact_limit, rule_limit=rule_limit)

        self.positives = set()
        # Negative facts are stored in positive looking form, not_greater(1,2) becomes greater(1,2)
        # This makes it easy to check if a candidate rule derived a known false fact
        self.negatives = set()
        self.constants = set()

        # predicate -> list[Rule]
        # Dictionary, keys are the predicate names,
        # values are rule templates generated for that predicate
        self.predicate_universe = {}

        # Rule -> metadata
        # Contains rule templates is considering but has not yet trusted, has metadata for each rule
        self.candidates = {}

        # rule templates we are confident in
        self.committed_rules = set()

    def is_negative(self, fact: Fact) -> bool:
        return fact.predicate.startswith("not_")

    def positive_version(self, fact: Fact) -> Fact:
        # Convert not_greater(1, 2) into greater(1, 2). Returns if given positive input

        if not self.is_negative(fact):
            return fact

        positive_predicate = fact.predicate.removeprefix("not_")
        return Fact(positive_predicate, fact.args)

    def ensure_predicate_universe(self, predicate: str) -> None:
        # Generates candidate rules the first time we see a predicate

        if predicate in self.predicate_universe:
            return

        rules = generate_universe(predicate)
        self.predicate_universe[predicate] = rules

        for r in rules:
            self.candidates[r] = {
                "support": 0,
                # support = how much evidence have I seen for this rule
                "eliminated": False,
                # eliminated = did this rule derive something known false
                "committed": False,
                # committed = have I decided to actually use this rule
            }

    def process(self, fact: Fact) -> None:
        """
        Processes one incoming fact
        Positive facts go into LogicMemory
        Negative facts are stored separately
        """
        for arg in fact.args:
            self.constants.add(arg)

        if self.is_negative(fact):
            negative_fact = self.positive_version(fact)
            self.negatives.add(negative_fact)
            self.ensure_predicate_universe(negative_fact.predicate)
            return

        self.positives.add(fact)
        self.memory.add_fact(fact)
        self.ensure_predicate_universe(fact.predicate)

        # TODO: Rule support / elimination

    def answer(self, query: Fact) -> str:
        # Answers using stored facts plus grounded versions of committed rules

        constants = set(self.constants)
        for arg in query.args:
            constants.add(arg)

        return ask_with_grounded_rules(
            facts=self.memory.facts.keys(),
            rule_templates=self.committed_rules,
            constants=constants,
            query=query,
        )

    def show(self) -> None:
        print("Positive facts:")
        for fact in sorted(self.positives, key=str):
            print(" ", fact)

        print("Negative facts:")
        for fact in sorted(self.negatives, key=str):
            print(" ", fact)

        print("Constants:")
        print(" ", sorted(self.constants))

        print("Candidates:")
        for rule, meta in self.candidates.items():
            print(" ", rule.name, rule, meta)

        print("Committed rules:")
        for rule in self.committed_rules:
            print(" ", rule)
