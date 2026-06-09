from typing import Any, Dict, Iterable, Optional, Tuple
from itertools import product
from z3 import (
    And,
    Bool,
    BoolSort,
    Const,
    DeclareSort,
    ForAll,
    Function,
    Implies,
    Not,
    Solver,
    unsat,
)
from facts import Fact, Rule

_entity_sort = None
_predicate_fns: Dict[str, Any] = {}
_entity_consts: Dict[str, Any] = {}


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


def is_variable(term: str) -> bool:
    # treats uppercase strings (X, Y, Z) as variables, everything else is treated as a constant
    return term.isalpha() and term.isupper()


def variables_in_fact(fact: Fact):
    return {arg for arg in fact.args if is_variable(arg)}


def variables_in_rule(rule: Rule):
    variables = set()

    for premise in rule.premises:
        variables.update(variables_in_fact(premise))
    variables.update(variables_in_fact(rule.conclusion))

    return sorted(variables)


def substitute_fact(fact: Fact, assignment: Dict[str, str]) -> Fact:
    """
    Replaces variables with their values
    Example:
        greater(X, Y), {"X": "5", "Y": "4}
        becomes greater(5, 4)
    """
    grounded_args = tuple(assignment.get(arg, arg) for arg in fact.args)
    return Fact(fact.predicate, grounded_args)


def ground_rule(rule: Rule, assignment: Dict[str, str]) -> Rule:
    grounded_premises = tuple(substitute_fact(p, assignment) for p in rule.premises)
    grounded_conclusion = substitute_fact(rule.conclusion, assignment)

    return Rule(
        premises=grounded_premises,
        conclusion=grounded_conclusion,
        name=rule.name,
    )


def _get_entity_sort():
    global _entity_sort
    if _entity_sort is None:
        _entity_sort = DeclareSort("Entity")
    return _entity_sort


def _entity(name: str):
    if name not in _entity_consts:
        _entity_consts[name] = Const(f"ent_{name}", _get_entity_sort())
    return _entity_consts[name]


def _predicate_fn(name: str):
    if name not in _predicate_fns:
        sort = _get_entity_sort()
        _predicate_fns[name] = Function(name, sort, sort, BoolSort())
    return _predicate_fns[name]


def _fact_atom(fact: Fact):
    pred = _predicate_fn(fact.predicate)
    return pred(_entity(fact.args[0]), _entity(fact.args[1]))


def _fact_pattern(fact: Fact, var_map: Dict[str, Any]):
    pred = _predicate_fn(fact.predicate)
    args = []
    for arg in fact.args:
        if is_variable(arg):
            if arg not in var_map:
                var_map[arg] = Const(arg, _get_entity_sort())
            args.append(var_map[arg])
        else:
            args.append(_entity(arg))
    return pred(*args)


def rule_to_z3_forall(rule: Rule):
    var_map: Dict[str, Any] = {}
    premises = [_fact_pattern(p, var_map) for p in rule.premises]
    conclusion = _fact_pattern(rule.conclusion, var_map)
    body = Implies(And(*premises), conclusion) if premises else conclusion
    z3_vars = list(var_map.values())
    if not z3_vars:
        return body
    return ForAll(z3_vars, body)


def build_solver_with_quantified_rules(
    facts: Iterable[Fact],
    rule_templates: Iterable[Rule],
    negatives: Iterable[Fact] = (),
):
    s = Solver()
    for fact in facts:
        s.add(_fact_atom(fact))
    for fact in negatives:
        s.add(Not(_fact_atom(fact)))
    for template in rule_templates:
        s.add(rule_to_z3_forall(template))
    return s


def ask_with_quantified_rules(
    facts: Iterable[Fact],
    rule_templates: Iterable[Rule],
    query: Fact,
    negatives: Iterable[Fact] = (),
) -> str:
    s = build_solver_with_quantified_rules(facts, rule_templates, negatives)
    q = _fact_atom(query)

    s.push()
    s.add(Not(q))
    if s.check() == unsat:
        s.pop()
        return "True"
    s.pop()

    s.push()
    s.add(q)
    if s.check() == unsat:
        s.pop()
        return "False"
    s.pop()

    return "Unknown"


def apply_rule(rule: Rule, premise_facts: Tuple[Fact, ...]) -> Optional[Fact]:
    """Ground a rule template using concrete premise facts; None if they do not match."""
    if len(rule.premises) == 0:
        return rule.conclusion

    subst: Dict[str, str] = {}
    for prem, fact in zip(rule.premises, premise_facts):
        if prem.predicate != fact.predicate or len(prem.args) != len(fact.args):
            return None
        for pattern_arg, fact_arg in zip(prem.args, fact.args):
            if is_variable(pattern_arg):
                if pattern_arg in subst and subst[pattern_arg] != fact_arg:
                    return None
                subst[pattern_arg] = fact_arg
            elif pattern_arg != fact_arg:
                return None
    return substitute_fact(rule.conclusion, subst)


def rule_derives_false_from_positives(
    rule: Rule,
    positives: Iterable[Fact],
    negatives: Iterable[Fact],
    constants: Iterable[str] = (),
) -> bool:
    """Check whether any positive-fact instance of rule derives a known false conclusion."""
    negative_set = set(negatives)
    pos_list = list(positives)

    if len(rule.premises) == 0:
        known_constants = set(constants) or {arg for fact in pos_list for arg in fact.args}
        for constant in known_constants:
            assignment = {var: constant for var in variables_in_fact(rule.conclusion)}
            conclusion = substitute_fact(rule.conclusion, assignment)
            if conclusion in negative_set:
                return True
        return False

    if len(rule.premises) == 1:
        for fact in pos_list:
            conclusion = apply_rule(rule, (fact,))
            if conclusion is not None and conclusion in negative_set:
                return True
        return False

    if len(rule.premises) == 2:
        for i, first in enumerate(pos_list):
            for second in pos_list[i + 1 :]:
                for pair in ((first, second), (second, first)):
                    conclusion = apply_rule(rule, pair)
                    if conclusion is not None and conclusion in negative_set:
                        return True
        return False

    return False


def ground_rules(rule: Rule, constants) -> list[Rule]:
    """
    Grounds a rule over all known constants
    Example:
        P(X,Y) AND P(Y,Z) -> P(X,Z)
        with constants {1, 2, 3} creates many concrete rules like:
        P(3,2) AND P(2,1) -> P(3,1)
    """
    variables = variables_in_rule(rule)

    if not variables:
        return [rule]

    grounded = []
    for values in product(constants, repeat=len(variables)):
        # zip makes (variable, value) pairs
        assignment = dict(zip(variables, values))
        grounded.append(ground_rule(rule, assignment))

    return grounded


def build_solver_with_grounded_rules(facts, rule_templates, constants):
    s = Solver()
    for fact in facts:
        s.add(fact_to_z3(fact))

    for rule_template in rule_templates:
        for grounded_rule in ground_rules(rule_template, constants):
            s.add(rule_to_z3(grounded_rule))

    return s


def ask_with_grounded_rules(facts, rule_templates, constants, query: Fact) -> str:
    s = build_solver_with_grounded_rules(facts, rule_templates, constants)
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
