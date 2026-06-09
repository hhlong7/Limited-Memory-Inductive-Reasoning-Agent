import csv
import time
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from agents import FOLCompressionAgent, ImportanceAgent, RandomAgent, SimpleAgent
from data import load_quiz, load_stream
from quiz import run_quiz


DATASET_FACT_LIMITS: Dict[str, int] = {
    "greater_chain_small": 20,
    "greater_chain_large": 52,
    "divisibility_chain_small": 10,
    "divisibility_chain_large": 47,
    "equals_chain_small": 10,
    "equals_chain_large": 50,
    "mixed_chain_small": 40,
    "mixed_chain_large": 105,
}

AGENTS: List[Tuple[str, Callable[[int], object]]] = [
    ("SimpleAgent", lambda fact_limit: SimpleAgent(fact_limit=fact_limit)),
    ("RandomAgent", lambda fact_limit: RandomAgent(fact_limit=fact_limit)),
    ("ImportanceAgent", lambda fact_limit: ImportanceAgent(fact_limit=fact_limit)),
    (
        "FOLCompressionAgent",
        lambda fact_limit: FOLCompressionAgent(fact_limit=fact_limit),
    ),
]

AGENT_ORDER = {name: idx for idx, (name, _) in enumerate(AGENTS)}


def run_agent(agent_name: str, factory: Callable[[int], object], dataset_dir: Path, fact_limit: int):
    stream = load_stream(dataset_dir / "stream.json")
    quiz_questions = load_quiz(dataset_dir / "quiz.json")

    agent = factory(fact_limit)

    for fact in stream:
        agent.process(fact)
    if hasattr(agent, "finalize"):
        agent.finalize()

    quiz_start = time.perf_counter()
    result = run_quiz(agent, quiz_questions, show_unknowns=False)
    quiz_time_sec = time.perf_counter() - quiz_start

    return {
        "dataset": dataset_dir.name,
        "agent": agent_name,
        "fact_limit": fact_limit,
        "correct": result.correct,
        "total": result.total,
        "accuracy": result.accuracy,
        "unknown_count": result.unknown_count,
        "quiz_time_sec": quiz_time_sec,
    }


def summarize_best(rows: List[dict]) -> None:
    dataset_groups: Dict[str, List[dict]] = {}
    for row in rows:
        dataset_groups.setdefault(row["dataset"], []).append(row)

    print("\nBest agent per dataset:")
    for dataset_name in sorted(dataset_groups.keys()):
        group = dataset_groups[dataset_name]
        best = max(
            group,
            key=lambda r: (r["accuracy"], -r["unknown_count"], -r["quiz_time_sec"]),
        )
        print(
            f"- {dataset_name}: {best['agent']} "
            f"(acc={best['accuracy']:.1%}, unknown={best['unknown_count']}, quiz_time={best['quiz_time_sec']:.4f}s)"
        )


def main():
    root = Path(__file__).parent
    datasets_root = root / "datasets"
    output_dir = root / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "benchmark.csv"

    rows = []

    for dataset_name, fact_limit in DATASET_FACT_LIMITS.items():
        dataset_dir = datasets_root / dataset_name
        if not dataset_dir.exists():
            raise FileNotFoundError(f"Missing dataset directory: {dataset_dir}")

        for agent_name, factory in AGENTS:
            row = run_agent(agent_name, factory, dataset_dir, fact_limit)
            rows.append(row)

    dataset_order = {name: idx for idx, name in enumerate(DATASET_FACT_LIMITS.keys())}
    rows.sort(key=lambda r: (dataset_order[r["dataset"]], AGENT_ORDER.get(r["agent"], 999)))

    fieldnames = [
        "dataset",
        "agent",
        "fact_limit",
        "correct",
        "total",
        "accuracy",
        "unknown_count",
        "quiz_time_sec",
    ]

    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "accuracy": f"{row['accuracy']:.6f}",
                    "quiz_time_sec": f"{row['quiz_time_sec']:.6f}",
                }
            )

    print(f"Benchmark results written to {output_csv}")
    summarize_best(rows)


if __name__ == "__main__":
    main()
