from collections import OrderedDict
from facts import Fact, Rule
from logic import (
    LogicMemory,
    ask_with_quantified_rules,
    build_solver_with_quantified_rules,
    rule_derives_false_from_positives,
    _fact_atom,
)
from z3 import Not, unsat
from universal import generate_universe, pair_index_pattern, shape_for_pattern, reflexivity_rule
from agents.base import BaseAgent


class FOLCompressionAgent(BaseAgent):
    def __init__(self, fact_limit: int = 20, rule_limit: int = 20):
        self.memory = LogicMemory(fact_limit=fact_limit, rule_limit=rule_limit)
        # Shared FIFO learning buffer: positives + negatives sum to fact_limit.
        self._learning_trace: OrderedDict[tuple[str, Fact], None] = OrderedDict()
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

    def _learning_positives(self):
        return [fact for kind, fact in self._learning_trace if kind == "pos"]

    def _learning_negatives(self):
        return {fact for kind, fact in self._learning_trace if kind == "neg"}

    def _add_learning(self, kind: str, fact: Fact) -> None:
        key = (kind, fact)
        if key in self._learning_trace:
            return
        if len(self._learning_trace) >= self.memory.fact_limit:
            self._learning_trace.popitem(last=False)
        self._learning_trace[key] = None

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

    def _memory_positives(self):
        return [fact for fact in self.memory.facts if not self.is_negative(fact)]

    def _memory_negatives(self):
        return {self.positive_version(fact) for fact in self.memory.facts if self.is_negative(fact)}

    def update_reflexivity_support(self, fact: Fact) -> None:
        """A reflexive positive fact is one vote for the reflexivity rule."""
        if len(fact.args) != 2 or fact.args[0] != fact.args[1]:
            return

        rule = reflexivity_rule(fact.predicate)
        if rule not in self.candidates:
            return

        meta = self.candidates[rule]
        if meta["eliminated"] or meta["committed"]:
            return
        meta["support"] += 1

    def update_support(self, new_fact: Fact) -> None:
        """Compare a new fact to stored positives; one vote per pair."""
        self.update_reflexivity_support(new_fact)

        for old_fact in self._learning_positives():
            if old_fact == new_fact:
                continue
            if old_fact.predicate != new_fact.predicate:
                continue

            rule = None
            for p1, p2 in ((old_fact, new_fact), (new_fact, old_fact)):
                pattern = pair_index_pattern(p1, p2)
                candidate = shape_for_pattern(new_fact.predicate, pattern)
                if candidate is None:
                    continue
                if candidate.name == "transitivity_chain":
                    rule = candidate
                    break
                if rule is None:
                    rule = candidate

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
            if rule_derives_false_from_positives(
                rule, self._learning_positives(), self._learning_negatives(), self.constants
            ):
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
            for fact in list(self._memory_positives()):
                other_facts = [f for f in self._memory_positives() if f != fact]
                res = ask_with_quantified_rules(
                    facts=[f for f in other_facts if not self.is_negative(f)],
                    rule_templates=self.committed_rules,
                    query=fact,
                    negatives=self._memory_negatives(),
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
            self.memory.add_fact(fact)
            self._invalidate_solver()
            self.ensure_predicate_universe(negative_fact.predicate)
            self._add_learning("neg", negative_fact)
            self.eliminate_candidates()
            self.track_plateau()
            self.maybe_commit()
            return

        self.memory.add_fact(fact)
        self._invalidate_solver()
        self.ensure_predicate_universe(fact.predicate)
        self.update_support(fact)
        self._add_learning("pos", fact)
        self.eliminate_candidates()
        # 4. Update plateau tracking for this fact
        self.track_plateau()
        # 5. Commit if counter and support are high enough
        self.maybe_commit()

    def _answer_positive(self, query: Fact) -> str:
        if self._solver is None:
            self._solver = build_solver_with_quantified_rules(
                self._memory_positives(),
                self.committed_rules,
                self._memory_negatives(),
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

    def answer(self, query: Fact) -> str:
        if self.is_negative(query):
            if self.memory.has_fact(query):
                return "True"
            positive = self.positive_version(query)
            if positive in self._memory_negatives():
                return "True"
            result = self._answer_positive(positive)
            if result == "True":
                return "False"
            if result == "False":
                return "True"
            return "Unknown"
        return self._answer_positive(query)

    def finalize(self) -> None:
        if self.committed_rules:
            return
        self.facts_since_support_change = self.plateau_threshold
        self.maybe_commit()

    def show(self) -> None:
        print(f"Learning trace ({len(self._learning_trace)}/{self.memory.fact_limit}):")
        for kind, fact in self._learning_trace:
            label = "pos" if kind == "pos" else "not"
            print(f"  [{label}] {fact}")

        print("Memory facts:")
        for fact in sorted(self.memory.facts, key=str):
            print(" ", fact)

        print("Constants:")
        print(" ", sorted(self.constants))

        print("Candidates:")
        for rule, meta in self.candidates.items():
            print(" ", rule.name, rule, meta)

        print("Committed rules:")
        for rule in self.committed_rules:
            print(" ", rule)
