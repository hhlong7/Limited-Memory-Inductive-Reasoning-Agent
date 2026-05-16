from dataclasses import dataclass
from typing import Tuple, Dict, Optional
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

        # keys are the actual stored Facts/Rules
        # values are metadata dictionaries for future scoring/counting
        self.facts: Dict[Fact, Dict[str, Any]] = {}
        self.rules: Dict[Rule, Dict[str, Any]] = {}

    # checks is we store this exact fact
    def has_fact(self, fact: Fact) -> bool:
        return fact in self.facts

    def has_rule(self, rule: Rule) -> bool:
        return rule in self.rules

    def add_fact(self, fact: Fact):
        if self.has_fact(fact):
            return

        if len(self.facts) >= self.fact_limit:
            oldest_fact = next(iter(self.facts))
            del self.facts[oldest_fact]

        self.facts[fact] = {
            "score": 0.0
        }

    def remove_fact(self, fact: Fact):
        if self.has_fact(fact):
            del self.facts[fact]

    def add_rule(self, rule: Rule):
        if self.has_rule(rule):
            return

        if len(self.rules) >= self.rule_limit:
            oldest_rule = next(iter(self.rules))
            del self.rules[oldest_rule]

        self.rules[rule] = {
            "support_count": 1,
            "score": 0.0,
        }

    def remove_rule(self, rule: Rule):
        if self.has_rule(rule):
            del self.rules[rule]

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
        self.show_facts()
        self.show_rules()

    def show_facts(self):
        print("Facts:")
        for fact, metadata in self.facts.items():
            print(" ", fact, metadata)

    def show_rules(self):
        print("Rules:")
        for rule, metadata in self.rules.items():
            print(" ", rule, metadata)


if __name__ == "__main__":
    memory = LogicMemory(fact_limit=20, rule_limit=5)

    greater_a_b = Fact("greater", ("a", "b"))
    greater_b_c = Fact("greater", ("b", "c"))
    greater_a_c = Fact("greater", ("a", "c"))
    greater_c_a = Fact("greater", ("c", "a"))

    memory.add_fact(greater_a_b)
    memory.add_fact(greater_b_c)

    transitive_example = Rule(
        premises=(
            greater_a_b,
            greater_b_c,
        ),
        conclusion=greater_a_c,
        name="example_transitive_greater"
    )

    memory.add_rule(transitive_example)

    memory.show_memory()

    print("Directly stored greater(a, b):", memory.has_fact(greater_a_b))
    print("Directly stored greater(a, c):", memory.has_fact(greater_a_c))
    print("Directly stored transitive rule:", memory.has_rule(transitive_example))

    print("Query greater(a, b):", memory.ask(greater_a_b))
    print("Query greater(a, c):", memory.ask(greater_a_c))
    print("Query greater(c, a):", memory.ask(greater_c_a))