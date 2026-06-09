"""
Run once to create fixed datasets used by all agents.
Re-running overwrites existing files — only do this intentionally.

Usage:
    uv run python generate_dataset.py
"""
import random
from pathlib import Path
from data import (
    generate_greater_chain_stream,
    generate_greater_transitive_quiz,
    generate_greater_negatives,
    generate_divides_negatives,
    generate_equals_stream,
    generate_equals_quiz,
    generate_equals_negatives,
    generate_mixed_divisibility_chain_stream,
    generate_mixed_divisibility_transitive_quiz,
    generate_mixed_chain_stream,
    generate_mixed_chain_quiz,
    save_stream,
    save_quiz,
)

DATASETS = {
    "greater_chain_small": {"max_n": 10, "n_negatives": 3, "stream_seed": 42, "quiz_seed": 99},
    "greater_chain_large": {"max_n": 50, "n_quiz": 500, "n_negatives": 3, "stream_seed": 42, "quiz_seed": 99},
    "divisibility_chain_small": {"bases": [2, 3], "length": 6, "n_negatives": 3, "stream_seed": 42, "quiz_seed": 99},
    "divisibility_chain_large": {"bases": [2, 3, 5, 7], "length": 12, "n_negatives": 3, "stream_seed": 42, "quiz_seed": 99},
    "equals_chain_small": {"max_n": 10, "n_quiz": 30, "n_negatives": 3, "stream_seed": 42, "quiz_seed": 99},
    "equals_chain_large": {"max_n": 50, "n_quiz": 150, "n_negatives": 3, "stream_seed": 42, "quiz_seed": 99},
    "mixed_chain_small": {
        "max_n": 10,
        "bases": [2, 3],
        "length": 6,
        "n_negatives": 3,
        "stream_seed": 42,
        "quiz_seed": 99,
    },
    "mixed_chain_large": {
        "max_n": 30,
        "bases": [2, 3, 5, 7],
        "length": 9,
        "n_negatives": 3,
        "n_quiz": 250,
        "equals_n_questions": 70,
        "stream_seed": 42,
        "quiz_seed": 99,
    },
}


def build_dataset(name, cfg):
    if name.startswith("greater_chain"):
        stream = generate_greater_chain_stream(
            max_n=cfg["max_n"],
            seed=cfg["stream_seed"],
        )
        negatives = generate_greater_negatives(
            max_n=cfg["max_n"],
            seed=cfg["stream_seed"] + 1,
            n_facts=cfg.get("n_negatives"),
        )
        stream = stream + negatives
        stream_rng = random.Random(cfg["stream_seed"] + 2)
        stream_rng.shuffle(stream)

        quiz = generate_greater_transitive_quiz(
            max_n=cfg["max_n"],
            seed=cfg["quiz_seed"],
            false_sources=negatives,
            n_questions=cfg.get("n_quiz"),
        )

    elif name.startswith("divisibility_chain"):
        stream = generate_mixed_divisibility_chain_stream(
            bases=cfg["bases"],
            length=cfg["length"],
            seed=cfg["stream_seed"],
        )
        negatives = generate_divides_negatives(
            bases=cfg["bases"],
            length=cfg["length"],
            seed=cfg["stream_seed"] + 1,
            n_facts=cfg.get("n_negatives"),
        )
        stream = stream + negatives
        stream_rng = random.Random(cfg["stream_seed"] + 2)
        stream_rng.shuffle(stream)

        quiz = generate_mixed_divisibility_transitive_quiz(
            bases=cfg["bases"],
            length=cfg["length"],
            seed=cfg["quiz_seed"],
            false_sources=negatives,
        )

    elif name.startswith("equals_chain"):
        stream = generate_equals_stream(
            max_n=cfg["max_n"],
            seed=cfg["stream_seed"],
        )
        negatives = generate_equals_negatives(
            max_n=cfg["max_n"],
            seed=cfg["stream_seed"] + 1,
            n_facts=cfg.get("n_negatives"),
        )
        stream = stream + negatives
        stream_rng = random.Random(cfg["stream_seed"] + 2)
        stream_rng.shuffle(stream)

        quiz = generate_equals_quiz(
            max_n=cfg["max_n"],
            n_questions=cfg["n_quiz"],
            seed=cfg["quiz_seed"],
            false_sources=negatives,
        )

    elif name.startswith("mixed_chain"):
        stream = generate_mixed_chain_stream(
            max_n=cfg["max_n"],
            bases=cfg["bases"],
            length=cfg["length"],
            seed=cfg["stream_seed"],
            n_negatives=cfg.get("n_negatives", 3),
        )
        quiz = generate_mixed_chain_quiz(
            max_n=cfg["max_n"],
            bases=cfg["bases"],
            length=cfg["length"],
            stream_seed=cfg["stream_seed"],
            quiz_seed=cfg["quiz_seed"],
            n_negatives=cfg.get("n_negatives", 3),
            equals_n_questions=cfg.get("equals_n_questions", 20),
            n_greater_questions=cfg.get("n_quiz"),
        )

    else:
        raise ValueError(f"Unknown dataset: {name}")

    return stream, quiz


def main():
    for name, cfg in DATASETS.items():
        out = Path("datasets") / name
        out.mkdir(parents=True, exist_ok=True)

        stream, quiz = build_dataset(name, cfg)

        save_stream(stream, out / "stream.json")
        save_quiz(quiz, out / "quiz.json")

        print(f"[{name}] stream={len(stream)} facts | quiz={len(quiz)} questions")
        if "max_n" in cfg:
            total_facts = cfg["max_n"] * (cfg["max_n"] - 1) // 2
            print(f"         max_n={cfg['max_n']} | {total_facts} possible greater facts")
        if "bases" in cfg:
            print(f"         bases={cfg['bases']} | length={cfg['length']}")
        print(f"         -> {out}/stream.json")
        print(f"         -> {out}/quiz.json")


if __name__ == "__main__":
    main()
