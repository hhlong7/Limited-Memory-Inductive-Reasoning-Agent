from typing import List
from facts import Fact, Rule

NAMES = (
    "transitivity_chain",
    "shared_first_arg",
    "shared_second_arg",
    "symmetry",
    "left_composition",
    "right_composition",
)

#generate rules for a given predicate

def rule(predicate: str) -> List[Rule]:
    p = predicate

    return [
        # P(X,Y) AND P(Y,Z) -> P(X,Z)
        Rule(
            premises=(Fact(p, ("X", "Y")), Fact(p, ("Y", "Z"))),
            conclusion=Fact(p, ("X", "Z")),
            name="transitivity_chain",
        ),

        # P(X,Y) AND P(X,Z) -> P(Y,Z)
        Rule(
            premises=(Fact(p, ("X", "Y")), Fact(p, ("X", "Z"))),
            conclusion=Fact(p, ("Y", "Z")),
            name="shared_first_arg",
        ),

        # P(X,Y) AND P(Z,Y) -> P(X,Z)
        Rule(
            premises=(Fact(p, ("X", "Y")), Fact(p, ("Z", "Y"))),
            conclusion=Fact(p, ("X", "Z")),
            name="shared_second_arg",
        ),

        # P(X,Y) -> P(Y,X)
        Rule(
            premises=(Fact(p, ("X", "Y")),),
            conclusion=Fact(p, ("Y", "X")),
            name="symmetry",
        ),

        # P(X,Y) AND P(Z,X) -> P(Z,Y)
        Rule(
            premises=(Fact(p, ("X", "Y")), Fact(p, ("Z", "X"))),
            conclusion=Fact(p, ("Z", "Y")),
            name="left_composition",
        ),

        # P(Y,X) AND P(Y,Z) -> P(X,Z)
        Rule(
            premises=(Fact(p, ("Y", "X")), Fact(p, ("Y", "Z"))),
            conclusion=Fact(p, ("X", "Z")),
            name="right_composition",
        ),
    ]

#give 2 facts, find the pattern of shared argv, and return the corresponding rule shape if it matches one of the predefined patterns, otherwise return None

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


#given a predicate and a pattern, return the corresponding rule shape if it matches one of the 
#predefined patterns: 
#(1, 0) -> transitivity_chain
#(0, 0) -> shared_first_arg
#(1, 1) -> shared_second_arg
#(0, 1) -> left_composition 
#if na then return None
def shape_for_pattern(predicate: str, pattern):

    if pattern is None:
        return None

    p = predicate

    if pattern == (1, 0):
        return Rule(
            premises=(Fact(p, ("X", "Y")), Fact(p, ("Y", "Z"))),
            conclusion=Fact(p, ("X", "Z")),
            name="transitivity_chain",
        )

    if pattern == (0, 0):
        return Rule(
            premises=(Fact(p, ("X", "Y")), Fact(p, ("X", "Z"))),
            conclusion=Fact(p, ("Y", "Z")),
            name="shared_first_arg",
        )

    if pattern == (1, 1):
        return Rule(
            premises=(Fact(p, ("X", "Y")), Fact(p, ("Z", "Y"))),
            conclusion=Fact(p, ("X", "Z")),
            name="shared_second_arg",
        )

    if pattern == (0, 1):
        return Rule(
            premises=(Fact(p, ("X", "Y")), Fact(p, ("Z", "X"))),
            conclusion=Fact(p, ("Z", "Y")),
            name="left_composition",
        )

    return None
