from typing import Any, Dict
from z3 import Bool, And, Implies, Not, Solver, unsat
from facts import Fact, Rule


# TODO: propositional encoding — each Fact becomes a unique boolean (e.g. Bool("greater_5_3")).
# This works for grounded facts but breaks for rules with variables: a rule like
# greater(X,Y) ∧ greater(Y,Z) → greater(X,Z) has no Z3 representation here because
# X, Y, Z are just treated as literal string constants, not logical variables.
# For FOLCompressionAgent, either ground rules over all known constants at storage time,
# or switch to Z3 ForAll/Function to express true quantified FOL.
def fact_to_z3(fact: Fact):
    args_name = "_".join(fact.args)
    return Bool(f"{fact.predicate}_{args_name}")


def rule_to_z3(rule: Rule):
    premise_exprs = [fact_to_z3(p) for p in rule.premises]
    conclusion_expr = fact_to_z3(rule.conclusion)

    if len(premise_exprs) == 0:
        return conclusion_expr
    if len(premise_exprs) == 1:
        return Implies(premise_exprs[0], conclusion_expr)
    return Implies(And(*premise_exprs), conclusion_expr)


class LogicMemory:
    def __init__(self, fact_limit: int = 20, rule_limit: int = 20):
        self.fact_limit = fact_limit
        self.rule_limit = rule_limit
        self.facts: Dict[Fact, Dict[str, Any]] = {}
        self.rules: Dict[Rule, Dict[str, Any]] = {}

    def has_fact(self, fact: Fact) -> bool:
        return fact in self.facts

    def has_rule(self, rule: Rule) -> bool:
        return rule in self.rules

    def add_fact(self, fact: Fact):
        if self.has_fact(fact):
            return
        if len(self.facts) >= self.fact_limit:
            # TODO: eviction policy is hardcoded to FIFO (oldest fact removed).
            # RandomAgent and ImportanceAgent need different strategies.
            # Consider accepting an eviction callable so each agent can plug in its own policy.
            del self.facts[next(iter(self.facts))]
        self.facts[fact] = {"score": 0.0}

    def remove_fact(self, fact: Fact):
        if self.has_fact(fact):
            del self.facts[fact]

    def add_rule(self, rule: Rule):
        if self.has_rule(rule):
            return
        if len(self.rules) >= self.rule_limit:
            del self.rules[next(iter(self.rules))]
        self.rules[rule] = {"support_count": 1, "score": 0.0}

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

    def ask(self, query: Fact) -> str:
        s = self.build_solver()
        q = fact_to_z3(query)

        s.push()
        s.add(Not(q))
        result = s.check()
        s.pop()
        if result == unsat:
            return "True"

        s.push()
        s.add(q)
        result = s.check()
        s.pop()
        if result == unsat:
            return "False"

        return "Unknown"

    def show_facts(self):
        print("Facts:")
        for fact, meta in self.facts.items():
            print(" ", fact, meta)

    def show_rules(self):
        print("Rules:")
        for rule, meta in self.rules.items():
            print(" ", rule, meta)

    def show(self):
        self.show_facts()
        self.show_rules()
