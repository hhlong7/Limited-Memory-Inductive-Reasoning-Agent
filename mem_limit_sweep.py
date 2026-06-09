import csv
import time
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from agents import FOLCompressionAgent, ImportanceAgent, RandomAgent, SimpleAgent
from data import load_quiz, load_stream
from quiz import run_quiz


# Hero-chart sweep config (3 datasets).
SWEEP_DATASETS: Dict[str, List[int]] = {
    "greater_chain_large": [5, 10, 15, 20, 30, 40, 52],
    "mixed_chain_small": [5, 10, 15, 20, 30, 40],
    "divisibility_chain_large": [5, 10, 15, 20, 30, 40, 47],
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
    # Quiet mode: no agent.show() output.
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


def print_sweep_highlights(rows: List[dict]) -> None:
    print("\nSweep highlights (best by dataset x fact_limit):")

    grouped: Dict[Tuple[str, int], List[dict]] = {}
    for row in rows:
        key = (row["dataset"], row["fact_limit"])
        grouped.setdefault(key, []).append(row)

    for dataset_name, limits in SWEEP_DATASETS.items():
        for fact_limit in limits:
            group = grouped[(dataset_name, fact_limit)]
            best = max(
                group,
                key=lambda r: (r["accuracy"], -r["unknown_count"], -r["quiz_time_sec"]),
            )
            print(
                f"- {dataset_name} @ {fact_limit}: {best['agent']} "
                f"(acc={best['accuracy']:.1%}, unknown={best['unknown_count']})"
            )


def main():
    root = Path(__file__).parent
    datasets_root = root / "datasets"
    output_dir = root / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "mem_limit_sweep.csv"

    rows = []

    for dataset_name, fact_limits in SWEEP_DATASETS.items():
        dataset_dir = datasets_root / dataset_name
        if not dataset_dir.exists():
            raise FileNotFoundError(f"Missing dataset directory: {dataset_dir}")

        for fact_limit in fact_limits:
            for agent_name, factory in AGENTS:
                row = run_agent(agent_name, factory, dataset_dir, fact_limit)
                rows.append(row)

    dataset_order = {name: idx for idx, name in enumerate(SWEEP_DATASETS.keys())}
    rows.sort(
        key=lambda r: (
            dataset_order[r["dataset"]],
            r["fact_limit"],
            AGENT_ORDER.get(r["agent"], 999),
        )
    )

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

    print(f"Memory-limit sweep results written to {output_csv}")
    print_sweep_highlights(rows)


if __name__ == "__main__":
    main()
