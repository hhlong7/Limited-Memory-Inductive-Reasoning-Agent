import json
import random
from pathlib import Path
from typing import List, Tuple
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


def generate_greater_transitive_quiz(max_n: int, n_questions: int, seed: int) -> List[Tuple[Fact, str]]:
    """
    Generates non-adjacent greater-than questions.

    Example:
        greater(5, 3)
        greater(10, 2)

    These are true, but they are not direct chain links. They require
    transitive reasoning if the stream only contains adjacent facts.
    """
    pairs = [
        (i, j)
        for i in range(1, max_n + 1)
        for j in range(1, max_n + 1)
        if i > j and i != j + 1
    ]

    rng = random.Random(seed)
    rng.shuffle(pairs)

    selected = pairs[:n_questions]
    return [(Fact("greater", (str(i), str(j))), "True") for i, j in selected]


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


def generate_mixed_divisibility_transitive_quiz(
    bases: List[int],
    length: int,
    n_questions: int,
    seed: int
) -> List[Tuple[Fact, str]]:
    """
    Generates quiz questions from multiple divisibility chains.
    """
    questions = []

    for base in bases:
        values = [base ** i for i in range(1, length + 1)]

        pairs = [
            (values[i], values[j])
            for i in range(len(values))
            for j in range(len(values))
            if j > i + 1
        ]

        questions.extend((Fact("divides", (str(a), str(b))), "True") for a, b in pairs)

    rng = random.Random(seed)
    rng.shuffle(questions)

    return questions[:n_questions]


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
