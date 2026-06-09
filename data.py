import json
import random
from pathlib import Path
from typing import List, Optional, Tuple
from facts import Fact


# --- generation ---

def generate_greater_stream(max_n: int, seed: int) -> List[Fact]:
    pairs = [(i, j) for i in range(1, max_n + 1) for j in range(1, max_n + 1) if i > j]
    rng = random.Random(seed)
    rng.shuffle(pairs)
    return [Fact("greater", (str(i), str(j))) for i, j in pairs]


def generate_greater_recall_quiz(max_n: int, n_questions: int, seed: int) -> List[Tuple[Fact, str]]:
    pairs = [(i, j) for i in range(1, max_n + 1) for j in range(1, max_n + 1) if i > j]
    rng = random.Random(seed)
    rng.shuffle(pairs)
    selected = pairs[:n_questions]
    return [(Fact("greater", (str(i), str(j))), "True") for i, j in selected]


def generate_greater_chain_stream(max_n: int, seed: int) -> List[Fact]:
    """
    Generates only adjacent greater-than facts.

    Example for max_n=5:
        greater(2, 1)
        greater(3, 2)
        greater(4, 3)
        greater(5, 4)

    These are the chain links. Longer greater-than facts can be inferred
    through transitivity, but are not directly stored in the stream.
    """
    pairs = [(i, i - 1) for i in range(2, max_n + 1)]

    rng = random.Random(seed)
    rng.shuffle(pairs)

    return [Fact("greater", (str(i), str(j))) for i, j in pairs]


def generate_greater_transitive_quiz(
    max_n: int,
    seed: int,
    false_sources: Optional[List[Fact]] = None,
    n_questions: Optional[int] = None,
) -> List[Tuple[Fact, str]]:
    """
    Quiz over unique transitive greater pairs plus stream not_greater facts.
    When n_questions is set, include all negatives and sample true pairs without
    replacement up to that total.
    """
    true_pairs = [
        (i, j)
        for i in range(1, max_n + 1)
        for j in range(1, max_n + 1)
        if i > j and i != j + 1
    ]
    if false_sources is not None:
        false_pairs = [
            (int(f.args[0]), int(f.args[1]))
            for f in false_sources
            if f.predicate == "not_greater"
        ]
    else:
        false_pairs = [
            (i, j)
            for i in range(1, max_n + 1)
            for j in range(1, max_n + 1)
            if i <= j
        ]

    rng = random.Random(seed)
    rng.shuffle(true_pairs)
    rng.shuffle(false_pairs)

    if n_questions is not None:
        n_false = min(len(false_pairs), n_questions)
        n_true = min(len(true_pairs), n_questions - n_false)
        true_pairs = true_pairs[:n_true]
        false_pairs = false_pairs[:n_false]

    quiz = [
        (Fact("greater", (str(i), str(j))), "True")
        for i, j in true_pairs
    ]
    quiz.extend(
        (Fact("not_greater", (str(i), str(j))), "True")
        for i, j in false_pairs
    )
    rng.shuffle(quiz)
    return quiz


def generate_greater_negatives(max_n: int, seed: int, n_facts: Optional[int] = None) -> List[Fact]:
    """
    Generates false greater-than statements as explicit negative facts.

    A pair (i, j) is negative for greater iff i <= j.
    Encoded as predicate: not_greater(i, j)
    """
    pairs = [
        (i, j)
        for i in range(1, max_n + 1)
        for j in range(1, max_n + 1)
        if i <= j
    ]

    rng = random.Random(seed)
    rng.shuffle(pairs)

    if n_facts is not None:
        pairs = pairs[:n_facts]

    return [Fact("not_greater", (str(i), str(j))) for i, j in pairs]


def generate_divides_negatives(
    bases: List[int],
    length: int,
    seed: int,
    n_facts: Optional[int] = None,
) -> List[Fact]:
    """
    Generates false divides statements as explicit negative facts.

    A pair (a, b) is negative for divides iff a does not divide b.
    Encoded as predicate: not_divides(a, b)
    """
    values = set()
    for base in bases:
        for i in range(1, length + 1):
            values.add(base ** i)

    pairs = [
        (str(a), str(b))
        for a in values
        for b in values
        if a != b and int(b) % int(a) != 0
    ]

    rng = random.Random(seed)
    rng.shuffle(pairs)

    if n_facts is not None:
        pairs = pairs[:n_facts]

    return [Fact("not_divides", (a, b)) for a, b in pairs]


def generate_equals_stream(max_n: int, seed: int) -> List[Fact]:
    """
    Numeric equality over integers 1..max_n.

    Only reflexive facts are true, e.g. equals(3, 3).
    """
    pairs = [(i, i) for i in range(1, max_n + 1)]
    rng = random.Random(seed)
    rng.shuffle(pairs)
    return [Fact("equals", (str(i), str(j))) for i, j in pairs]


def generate_equals_quiz(
    max_n: int,
    n_questions: int,
    seed: int,
    false_sources: Optional[List[Fact]] = None,
) -> List[Tuple[Fact, str]]:
    """
    Mixed recall: equals(i, i) -> True and not_equals(i, j) -> True for i != j.
    """
    true_pairs = [(i, i) for i in range(1, max_n + 1)]
    if false_sources is not None:
        false_pairs = [
            (int(f.args[0]), int(f.args[1]))
            for f in false_sources
            if f.predicate == "not_equals"
        ]
    else:
        false_pairs = [
            (i, j)
            for i in range(1, max_n + 1)
            for j in range(1, max_n + 1)
            if i != j
        ]

    rng = random.Random(seed)
    rng.shuffle(true_pairs)
    rng.shuffle(false_pairs)

    n_true = min(n_questions // 2, len(true_pairs))
    n_false = min(n_questions - n_true, len(false_pairs))
    if n_true + n_false < n_questions:
        n_false = min(n_false + (n_questions - n_true - n_false), len(false_pairs))

    quiz = [
        (Fact("equals", (str(i), str(j))), "True")
        for i, j in true_pairs[:n_true]
    ]
    quiz.extend(
        (Fact("not_equals", (str(i), str(j))), "True")
        for i, j in false_pairs[:n_false]
    )
    rng.shuffle(quiz)
    return quiz


def generate_equals_negatives(
    max_n: int,
    seed: int,
    n_facts: Optional[int] = None,
) -> List[Fact]:
    """
    False equals statements as explicit negative facts.

    A pair (i, j) is negative for equals iff i != j.
    Encoded as predicate: not_equals(i, j)
    """
    pairs = [
        (i, j)
        for i in range(1, max_n + 1)
        for j in range(1, max_n + 1)
        if i != j
    ]

    rng = random.Random(seed)
    rng.shuffle(pairs)

    if n_facts is not None:
        pairs = pairs[:n_facts]

    return [Fact("not_equals", (str(i), str(j))) for i, j in pairs]


def generate_divisibility_chain_stream(base: int, length: int, seed: int) -> List[Fact]:
    """
    Generates a divisibility chain using powers of the base.

    Example for base=2, length=5:
        values = [2, 4, 8, 16, 32]

    Stream:
        divides(2, 4)
        divides(4, 8)
        divides(8, 16)
        divides(16, 32)

    Longer divisibility facts like divides(2, 16) are true, but not
    directly included in the stream.
    """
    values = [base ** i for i in range(1, length + 1)]
    pairs = [(values[i], values[i + 1]) for i in range(len(values) - 1)]

    rng = random.Random(seed)
    rng.shuffle(pairs)

    return [Fact("divides", (str(a), str(b))) for a, b in pairs]


def generate_divisibility_transitive_quiz(base: int, length: int, n_questions: int, seed: int) -> List[Tuple[Fact, str]]:
    """
    Generates divisibility questions that require skipping over at least
    one intermediate value.

    Example:
        divides(2, 8)
        divides(2, 16)
        divides(4, 32)
    """
    values = [base ** i for i in range(1, length + 1)]

    pairs = [
        (values[i], values[j])
        for i in range(len(values))
        for j in range(len(values))
        if j > i + 1
    ]

    rng = random.Random(seed)
    rng.shuffle(pairs)

    selected = pairs[:n_questions]
    return [(Fact("divides", (str(a), str(b))), "True") for a, b in selected]


def generate_mixed_divisibility_chain_stream(bases: List[int], length: int, seed: int) -> List[Fact]:
    """
    Generates multiple divisibility chains.

    Example with bases=[2, 3]:

        2-chain:
            divides(2, 4)
            divides(4, 8)
            divides(8, 16)

        3-chain:
            divides(3, 9)
            divides(9, 27)
            divides(27, 81)

    This gives the dataset more variety while still preserving the same
    transitivity pattern.
    """
    stream = []

    for base in bases:
        stream.extend(generate_divisibility_chain_stream(base, length, seed))

    rng = random.Random(seed)
    rng.shuffle(stream)

    return stream


def _divisibility_value_set(bases: List[int], length: int) -> set:
    values = set()
    for base in bases:
        for i in range(1, length + 1):
            values.add(base ** i)
    return values


def generate_mixed_divisibility_transitive_quiz(
    bases: List[int],
    length: int,
    seed: int,
    false_sources: Optional[List[Fact]] = None,
) -> List[Tuple[Fact, str]]:
    """
    Quiz over all unique transitive divides pairs plus stream not_divides facts.
    """
    values = _divisibility_value_set(bases, length)
    value_list = sorted(values)

    true_pairs = []
    seen = set()
    for base in bases:
        chain = [base ** i for i in range(1, length + 1)]
        for i in range(len(chain)):
            for j in range(len(chain)):
                if j > i + 1:
                    pair = (chain[i], chain[j])
                    if pair not in seen:
                        seen.add(pair)
                        true_pairs.append(pair)

    if false_sources is not None:
        false_pairs = [
            (int(f.args[0]), int(f.args[1]))
            for f in false_sources
            if f.predicate == "not_divides"
        ]
    else:
        false_pairs = [
            (a, b)
            for a in value_list
            for b in value_list
            if a != b and b % a != 0
        ]

    rng = random.Random(seed)
    rng.shuffle(true_pairs)
    rng.shuffle(false_pairs)

    quiz = [
        (Fact("divides", (str(a), str(b))), "True")
        for a, b in true_pairs
    ]
    quiz.extend(
        (Fact("not_divides", (str(a), str(b))), "True")
        for a, b in false_pairs
    )
    rng.shuffle(quiz)
    return quiz


# --- serialization ---

def save_stream(stream: List[Fact], path: Path) -> None:
    data = [{"predicate": f.predicate, "args": list(f.args)} for f in stream]
    path.write_text(json.dumps(data, indent=2))


def save_quiz(quiz: List[Tuple[Fact, str]], path: Path) -> None:
    data = [{"predicate": f.predicate, "args": list(f.args), "expected": e} for f, e in quiz]
    path.write_text(json.dumps(data, indent=2))


def load_stream(path: Path) -> List[Fact]:
    data = json.loads(path.read_text())
    return [Fact(d["predicate"], tuple(d["args"])) for d in data]


def load_quiz(path: Path) -> List[Tuple[Fact, str]]:
    data = json.loads(path.read_text())
    return [(Fact(d["predicate"], tuple(d["args"])), d["expected"]) for d in data]
