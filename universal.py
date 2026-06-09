from typing import List, Optional, Tuple
from facts import Fact, Rule

# Each spec defines one candidate rule template for any binary predicate P.
# pattern: (i, j) indexes for pair_index_pattern voting, or None if not pair-votable.
RuleSpec = Tuple[str, Optional[Tuple[int, int]], Tuple[Tuple[str, ...], ...], Tuple[str, ...]]

RULE_SPECS: List[RuleSpec] = [
    (
        "shared_first_arg",
        (0, 0),
        # P(X,Y) AND P(X,Z) -> P(Y,Z)
        (("X", "Y"), ("X", "Z")),
        ("Y", "Z"),
    ),
    (
        "shared_second_arg",
        (1, 1),
        # P(X,Y) AND P(Z,Y) -> P(X,Z)
        (("X", "Y"), ("Z", "Y")),
        ("X", "Z"),
    ),
    (
        "reflexivity",
        None,
        # -> P(X, X)
        (),
        ("X", "X"),
    ),
    (
        "symmetry",
        None,
        # P(X,Y) -> P(Y,X)
        (("X", "Y"),),
        ("Y", "X"),
    ),
    (
        "transitivity_chain",
        (1, 0),
        # P(X,Y) AND P(Y,Z) -> P(X,Z)
        (("X", "Y"), ("Y", "Z")),
        ("X", "Z"),
    ),
    (
        "left_composition",
        (0, 1),
        # P(X,Y) AND P(Z,X) -> P(Z,Y)
        (("X", "Y"), ("Z", "X")),
        ("Z", "Y"),
    ),
    (
        "right_composition",
        None,
        # P(Y,X) AND P(Y,Z) -> P(X,Z)
        # Same (0,0) pair pattern as shared_first_arg under renaming; kept in universe only.
        (("Y", "X"), ("Y", "Z")),
        ("X", "Z"),
    ),
]

NAMES = tuple(name for name, _, _, _ in RULE_SPECS)

_PATTERN_LOOKUP = {pattern: spec for spec in RULE_SPECS if (pattern := spec[1]) is not None}


def _build_rule(predicate: str, spec: RuleSpec) -> Rule:
    name, _, premise_arg_lists, conclusion_args = spec
    return Rule(
        premises=tuple(Fact(predicate, args) for args in premise_arg_lists),
        conclusion=Fact(predicate, conclusion_args),
        name=name,
    )


# generate rules for a given predicate (Horn clauses with at most 2 premises, plus reflexivity)
def generate_universe(predicate: str) -> List[Rule]:
    return [_build_rule(predicate, spec) for spec in RULE_SPECS]


def reflexivity_rule(predicate: str) -> Rule:
    return _build_rule(predicate, next(spec for spec in RULE_SPECS if spec[0] == "reflexivity"))


# give 2 facts, find the pattern of shared argv,
# and return the corresponding rule shape if it matches one of the predefined patterns,
# otherwise return None
def pair_index_pattern(g: Fact, f: Fact):
    if g.predicate != f.predicate:
        return None
    if len(g.args) != 2 or len(f.args) != 2:
        return None

    matches = []
    for i in range(2):
        for j in range(2):
            if g.args[i] == f.args[j]:
                matches.append((i, j))

    if len(matches) != 1:
        return None

    return matches[0]


# given a predicate and a pattern, return the corresponding rule shape if it matches one of the
# predefined patterns:
# (1, 0) -> transitivity_chain
# (0, 0) -> shared_first_arg
# (1, 1) -> shared_second_arg
# (0, 1) -> left_composition
# if na then return None
def shape_for_pattern(predicate: str, pattern):
    if pattern is None:
        return None
    spec = _PATTERN_LOOKUP.get(pattern)
    if spec is None:
        return None
    return _build_rule(predicate, spec)
