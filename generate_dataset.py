"""
Run once to create fixed datasets used by all agents.
Re-running overwrites existing files — only do this intentionally.

Usage:
    uv run python generate_dataset.py
"""
from pathlib import Path
from data import generate_greater_stream, generate_quiz, save_stream, save_quiz

DATASETS = {
    "small": {"max_n": 10, "n_quiz": 30, "stream_seed": 42, "quiz_seed": 99},
    "large": {"max_n": 15, "n_quiz": 50, "stream_seed": 42, "quiz_seed": 99},
}


def main():
    for name, cfg in DATASETS.items():
        out = Path("datasets") / name
        out.mkdir(parents=True, exist_ok=True)

        stream = generate_greater_stream(max_n=cfg["max_n"], seed=cfg["stream_seed"])
        quiz = generate_quiz(max_n=cfg["max_n"], n_questions=cfg["n_quiz"], seed=cfg["quiz_seed"])

        save_stream(stream, out / "stream.json")
        save_quiz(quiz, out / "quiz.json")

        total_facts = cfg["max_n"] * (cfg["max_n"] - 1) // 2
        print(f"[{name}] max_n={cfg['max_n']} | stream={len(stream)} facts ({total_facts} possible) | quiz={len(quiz)} questions")
        print(f"         -> {out}/stream.json")
        print(f"         -> {out}/quiz.json")


if __name__ == "__main__":
    main()
