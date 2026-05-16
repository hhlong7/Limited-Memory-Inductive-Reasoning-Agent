from dataclasses import dataclass
from typing import Tuple, List, Optional
from z3 import *


@dataclass(frozen=True)
class Fact:
    predicate: str
    args: Tuple[str, ...]

    def __str__(self):
        return f"{self.predicate}({', '.join(self.args)})"


@dataclass(frozen=True)
class Rule:
    premises: Tuple[Fact, ...]
    conclusion: Fact
    name: Optional[str] = None

    def __str__(self):
        left = " AND ".join(str(p) for p in self.premises)
        return f"{left} -> {self.conclusion}"


def fact_to_z3(fact: Fact):
    args_name = "_".join(fact.args)
    return Bool(f"{fact.predicate}_{args_name}")


def rule_to_z3(rule: Rule):
    premise_expressions = [fact_to_z3(premise) for premise in rule.premises]
    conclusion_expression = fact_to_z3(rule.conclusion)

    if len(premise_expressions) == 0:
        return conclusion_expression

    if len(premise_expressions) == 1:
        return Implies(premise_expressions[0], conclusion_expression)

    return Implies(And(*premise_expressions), conclusion_expression)


class LogicMemory:
    def __init__(self, fact_limit: int = 20, rule_limit: int = 20):
        self.fact_limit = fact_limit
        self.rule_limit = rule_limit
        self.facts: List[Fact] = []
        self.rules: List[Rule] = []

    def add_fact(self, fact: Fact):
        if fact in self.facts:
            return

        if len(self.facts) >= self.fact_limit:
            self.facts.pop(0)

        self.facts.append(fact)

    def remove_fact(self, fact: Fact):
        if fact in self.facts:
            self.facts.remove(fact)

    def add_rule(self, rule: Rule):
        if rule in self.rules:
            return

        if len(self.rules) >= self.rule_limit:
            self.rules.pop(0)

        self.rules.append(rule)

    def remove_rule(self, rule: Rule):
        if rule in self.rules:
            self.rules.remove(rule)

    def build_solver(self):
        s = Solver()

        for fact in self.facts:
            s.add(fact_to_z3(fact))

        for rule in self.rules:
            s.add(rule_to_z3(rule))

        return s

    # checks if given query can be proven from stored facts and rules
    # true if query is entailed by memory, false if query contradicts memory, unknown otherwise
    def ask(self, query: Fact) -> str:
        s = self.build_solver()
        query_expression = fact_to_z3(query)

        # push and pop for temporary inclusion of !query
        s.push()
        s.add(Not(query_expression))
        result = s.check()
        s.pop()

        # "does !query contradict my knowledge base? if yes, query == true"
        if result == unsat:
            return "True"

        s.push()
        s.add(query_expression)
        result = s.check()
        s.pop()

        # "does query contradict my knowledge base? if yes, query == false"
        if result == unsat:
            return "False"

        return "Unknown"

    def show_memory(self):
        print("Facts:")
        for fact in self.facts:
            print(" ", fact)

        print("Rules:")
        for rule in self.rules:
            print(" ", rule)

    def show_facts(self):
        print("Facts:")
        for fact in self.facts:
            print(" ", fact)

    def show_rules(self):
        print("Rules:")
        for rule in self.rules:
            print(" ", rule)


if __name__ == "__main__":
    memory = LogicMemory(fact_limit=20, rule_limit=5)

    memory.add_fact(Fact("greater", ("a", "b")))
    memory.add_fact(Fact("greater", ("b", "c")))

    memory.add_rule(
        Rule(
            premises=(
                Fact("greater", ("a", "b")),
                Fact("greater", ("b", "c")),
            ),
            conclusion=Fact("greater", ("a", "c")),
            name="example_transitive_greater"
        )
    )

    memory.show_memory()

    print("Query greater(a, b):", memory.ask(Fact("greater", ("a", "b"))))
    print("Query greater(a, c):", memory.ask(Fact("greater", ("a", "c"))))
    print("Query greater(c, a):", memory.ask(Fact("greater", ("c", "a"))))
