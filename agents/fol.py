from facts import Fact, Rule
from logic import (
    LogicMemory,
    ask_with_quantified_rules,
    build_solver_with_quantified_rules,
    rule_derives_false_from_positives,
    _fact_atom,
)
from z3 import Not, unsat
from universal import generate_universe, pair_index_pattern, shape_for_pattern
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
        # best rule
        self.prev_best_support = 0
        # number of facts since the best rule's support changed
        self.facts_since_support_change = 0
        # how many facts must pass without increase in best rule support before committing
        self.plateau_threshold = 2
        # minimum support required to commit a rule
        self.support_threshold = 3
        self._solver = None

    def _invalidate_solver(self) -> None:
        self._solver = None

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

    def update_support(self, new_fact: Fact) -> None:
        '''Compare a new fact to stored facts and increment support for matching rules'''
        for old_fact in self.positives:
            if old_fact == new_fact:
                continue
            if old_fact.predicate != new_fact.predicate:
                continue
            pattern = pair_index_pattern(old_fact, new_fact)
            rule = shape_for_pattern(new_fact.predicate, pattern)
            if rule is None or rule not in self.candidates:
                continue
            meta = self.candidates[rule]
            if meta["eliminated"] or meta["committed"]:
                continue
            meta["support"] += 1

    def eliminate_candidates(self) -> None:
        '''Eliminate templates for rules that derive a known false fact'''
        for rule, meta in self.candidates.items():
            if meta["eliminated"] or meta["committed"]:
                continue
            if rule_derives_false_from_positives(rule, self.positives, self.negatives):
                meta["eliminated"] = True

    def select_best_candidate(self) -> None:
        '''Return the best non-eliminated, non-committed rule and its support'''
        best_rule = None
        best_support = 0
        for rule, meta in self.candidates.items():
            if meta["eliminated"] or meta["committed"]:
                continue
            if meta["support"] > best_support:
                best_support = meta["support"]
                best_rule = rule
        return best_rule, best_support

    def track_plateau(self) -> None:
        '''Sees if the best rule's evidence has stopped growing'''
        best = max((
            meta["support"] for meta in self.candidates.values() if not meta["eliminated"] and not meta["committed"]
        ), default=0)

        if best != self.prev_best_support:
            self.prev_best_support = best
            self.facts_since_support_change = 0
        else:
            self.facts_since_support_change += 1


    def maybe_commit(self) -> None:
        '''Commits the best rule if plateauing (at most one rule total)'''
        if self.committed_rules:
            return
        if self.prev_best_support < self.support_threshold:
            return
        if self.facts_since_support_change < self.plateau_threshold:
            return
        
        best_rule = None
        best_support = 0
        for rule, meta in self.candidates.items():
            if meta["eliminated"] or meta["committed"]:
                continue
            if meta["support"] > best_support:
                best_support = meta["support"]
                best_rule = rule
        if best_rule is None or best_support < self.support_threshold:
            return

        meta = self.candidates[best_rule]
        meta["committed"] = True
        self.committed_rules.add(best_rule)
        self.memory.add_rule(best_rule)
        self._invalidate_solver()
        self.evict_derivable_facts()

    def evict_derivable_facts(self) -> None:
        '''Evicts facts that are derivable from committed rules (entailed)'''
        changed = True
        while changed:
            changed = False
            for fact in list(self.memory.facts.keys()):
                other_facts = [f for f in self.memory.facts.keys() if f != fact]
                res = ask_with_quantified_rules(
                    facts=other_facts,
                    rule_templates=self.committed_rules,
                    query=fact,
                )
                if res == "True":
                    self.memory.remove_fact(fact)
                    self._invalidate_solver()
                    changed = True

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
            self.eliminate_candidates()
            self.track_plateau()
            self.maybe_commit()
            return

        self.positives.add(fact)
        # 1. Remember the fact
        self.memory.add_fact(fact)
        self._invalidate_solver()
        self.ensure_predicate_universe(fact.predicate)
        # 2. Learn from opairs
        self.update_support(fact)
        # 3. Kill off bad rules
        self.eliminate_candidates()
        # 4. Update plateau tracking for this fact
        self.track_plateau()
        # 5. Commit if counter and support are high enough
        self.maybe_commit()

    def answer(self, query: Fact) -> str:
        if self._solver is None:
            self._solver = build_solver_with_quantified_rules(
                self.memory.facts.keys(),
                self.committed_rules,
            )

        s = self._solver
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

    def finalize(self) -> None:
        if self.committed_rules:
            return
        self.facts_since_support_change = self.plateau_threshold
        self.maybe_commit()

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
