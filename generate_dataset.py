"""
Run once to create fixed datasets used by all agents.
Re-running overwrites existing files — only do this intentionally.

Usage:
    uv run python generate_dataset.py
"""
from pathlib import Path
from data import (
    generate_greater_stream,
    generate_greater_recall_quiz,
    generate_greater_chain_stream,
    generate_greater_transitive_quiz,
    generate_mixed_divisibility_chain_stream,
    generate_mixed_divisibility_transitive_quiz,
    save_stream,
    save_quiz,
)

DATASETS = {
    "small": {"max_n": 10, "n_quiz": 30, "stream_seed": 42, "quiz_seed": 99},
    "large": {"max_n": 15, "n_quiz": 50, "stream_seed": 42, "quiz_seed": 99},
    "greater_chain_small": {"max_n": 10, "n_quiz": 30, "stream_seed": 42, "quiz_seed": 99},
    "greater_chain_large": {"max_n": 50, "n_quiz": 150, "stream_seed": 42, "quiz_seed": 99},
    "divisibility_chain_small": {"bases": [2, 3], "length": 6, "n_quiz": 20, "stream_seed": 42, "quiz_seed": 99},
    "divisibility_chain_large": {"bases": [2, 3, 5, 7], "length": 12, "n_quiz": 100, "stream_seed": 42, "quiz_seed": 99},
}


def build_dataset(name, cfg):
    if name.startswith("greater_chain"):
        stream = generate_greater_chain_stream(
            max_n=cfg["max_n"],
            seed=cfg["stream_seed"],
        )
        quiz = generate_greater_transitive_quiz(
            max_n=cfg["max_n"],
            n_questions=cfg["n_quiz"],
            seed=cfg["quiz_seed"],
        )

    elif name.startswith("divisibility_chain"):
        stream = generate_mixed_divisibility_chain_stream(
            bases=cfg["bases"],
            length=cfg["length"],
            seed=cfg["stream_seed"],
        )
        quiz = generate_mixed_divisibility_transitive_quiz(
            bases=cfg["bases"],
            length=cfg["length"],
            n_questions=cfg["n_quiz"],
            seed=cfg["quiz_seed"],
        )

    else:
        stream = generate_greater_stream(
            max_n=cfg["max_n"],
            seed=cfg["stream_seed"],
        )
        quiz = generate_greater_recall_quiz(
            max_n=cfg["max_n"],
            n_questions=cfg["n_quiz"],
            seed=cfg["quiz_seed"],
        )

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
