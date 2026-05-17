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


def generate_quiz(max_n: int, n_questions: int, seed: int) -> List[Tuple[Fact, str]]:
    pairs = [(i, j) for i in range(1, max_n + 1) for j in range(1, max_n + 1) if i > j]
    rng = random.Random(seed)
    rng.shuffle(pairs)
    selected = pairs[:n_questions]
    return [(Fact("greater", (str(i), str(j))), "True") for i, j in selected]


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
