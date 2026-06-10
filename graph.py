from __future__ import annotations

import argparse
import csv
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

_MPL_CONFIG_DIR = Path(tempfile.gettempdir()) / "limited-memory-agent-matplotlib"
_MPL_CONFIG_DIR.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG_DIR))

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "matplotlib is required to generate graphs. "
        "Install dependencies with `uv sync` after adding matplotlib."
    ) from exc


AGENT_ORDER = [
    "SimpleAgent",
    "RandomAgent",
    "ImportanceAgent",
    "FOLCompressionAgent",
]

AGENT_LABELS = {
    "SimpleAgent": "Simple",
    "RandomAgent": "Random",
    "ImportanceAgent": "Importance",
    "FOLCompressionAgent": "FOL Compression",
}

AGENT_COLORS = {
    "SimpleAgent": "#4C78A8",
    "RandomAgent": "#F58518",
    "ImportanceAgent": "#54A24B",
    "FOLCompressionAgent": "#1F9ED4",
}

DATASET_ORDER = [
    "greater_chain_small",
    "greater_chain_large",
    "divisibility_chain_small",
    "divisibility_chain_large",
    "equals_chain_small",
    "equals_chain_large",
    "mixed_chain_small",
    "mixed_chain_large",
]

def pretty_dataset_name(dataset_name: str) -> str:
    return dataset_name.replace("_", " ").title()


def slugify_dataset_list(dataset_names: list[str]) -> str:
    return "__".join(dataset_names)


def timestamped_filename(stem: str, timestamp: str) -> str:
    return f"{stem}_{timestamp}.png"


def load_csv_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                {
                    "dataset": row["dataset"],
                    "agent": row["agent"],
                    "fact_limit": int(row["fact_limit"]),
                    "correct": int(row["correct"]),
                    "total": int(row["total"]),
                    "accuracy": float(row["accuracy"]),
                    "accuracy_pct": float(row["accuracy"]) * 100.0,
                    "unknown_count": int(row["unknown_count"]),
                    "quiz_time_sec": float(row["quiz_time_sec"]),
                }
            )
    return rows


def dedupe_rows(rows: Iterable[dict], key_fields: tuple[str, ...]) -> list[dict]:
    deduped: dict[tuple, dict] = {}
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        deduped[key] = row
    return list(deduped.values())


def ordered_agents(rows: Iterable[dict]) -> list[str]:
    present = {row["agent"] for row in rows}
    return [agent for agent in AGENT_ORDER if agent in present]


def ordered_datasets(rows: Iterable[dict]) -> list[str]:
    present = {row["dataset"] for row in rows}
    ordered = [dataset for dataset in DATASET_ORDER if dataset in present]
    leftovers = sorted(present - set(ordered))
    return ordered + leftovers


def require_dataset(rows: list[dict], dataset_name: str, csv_label: str) -> None:
    available = ordered_datasets(rows)
    if dataset_name in available:
        return
    available_str = ", ".join(available) if available else "none"
    raise ValueError(
        f"Dataset '{dataset_name}' was not found in {csv_label}. "
        f"Available datasets: {available_str}"
    )


def annotate_bars_horizontal(ax, bars) -> None:
    for bar in bars:
        value = bar.get_width()
        y_pos = bar.get_y() + bar.get_height() / 2
        ax.text(
            min(value + 1.2, 98.0),
            y_pos,
            f"{value:.1f}%",
            va="center",
            ha="left",
            fontsize=9,
        )


def annotate_bars_vertical(ax, bars) -> None:
    for bar in bars:
        value = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            min(value + 1.5, 98.0),
            f"{value:.1f}%",
            va="bottom",
            ha="center",
            fontsize=8,
            rotation=90,
        )


def plot_hero_chart(rows: list[dict], dataset_name: str, output_path: Path) -> None:
    dataset_rows = [row for row in rows if row["dataset"] == dataset_name]
    if not dataset_rows:
        raise ValueError(f"No benchmark data found for dataset '{dataset_name}'.")

    agents = ordered_agents(dataset_rows)
    values = [
        next(row["accuracy_pct"] for row in dataset_rows if row["agent"] == agent)
        for agent in agents
    ]
    labels = [AGENT_LABELS[agent] for agent in agents]
    colors = [AGENT_COLORS[agent] for agent in agents]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(labels, values, color=colors)

    ax.set_title(f"Accuracy by Agent on {pretty_dataset_name(dataset_name)}", fontsize=16)
    ax.set_xlabel("Accuracy (%)")
    ax.set_xlim(0, 100)
    annotate_bars_horizontal(ax, bars)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_all_datasets_grouped(
    rows: list[dict], output_path: Path, dataset_names: list[str] | None = None
) -> None:
    datasets = ordered_datasets(rows)
    title = "Accuracy Across All Datasets"
    if dataset_names:
        for dataset_name in dataset_names:
            require_dataset(rows, dataset_name, "benchmark CSV")
        datasets = [dataset for dataset in datasets if dataset in dataset_names]
        title = "Accuracy Across Selected Datasets"
    agents = ordered_agents(rows)

    bar_height = 0.18
    y_positions = list(range(len(datasets)))
    offsets = [
        (index - (len(agents) - 1) / 2) * bar_height for index in range(len(agents))
    ]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    for offset, agent in zip(offsets, agents):
        values = []
        for dataset in datasets:
            match = next(
                row
                for row in rows
                if row["dataset"] == dataset and row["agent"] == agent
            )
            values.append(match["accuracy_pct"])

        ax.barh(
            [y + offset for y in y_positions],
            values,
            height=bar_height,
            label=AGENT_LABELS[agent],
            color=AGENT_COLORS[agent],
        )

    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Accuracy (%)")
    ax.set_ylabel("Dataset")
    ax.set_xlim(0, 100)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([pretty_dataset_name(dataset) for dataset in datasets])
    ax.invert_yaxis()
    ax.legend(ncols=2, frameon=False)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_memory_tradeoff(rows: list[dict], dataset_name: str, output_path: Path) -> None:
    dataset_rows = [row for row in rows if row["dataset"] == dataset_name]
    if not dataset_rows:
        raise ValueError(f"No sweep data found for dataset '{dataset_name}'.")

    agents = ordered_agents(dataset_rows)
    fact_limits = sorted({row["fact_limit"] for row in dataset_rows})
    x_positions = list(range(len(fact_limits)))
    bar_width = 0.18
    offsets = [
        (index - (len(agents) - 1) / 2) * bar_width for index in range(len(agents))
    ]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(11, 6))

    for offset, agent in zip(offsets, agents):
        values = []
        for fact_limit in fact_limits:
            match = next(
                row
                for row in dataset_rows
                if row["agent"] == agent and row["fact_limit"] == fact_limit
            )
            values.append(match["accuracy_pct"])

        bars = ax.bar(
            [x + offset for x in x_positions],
            values,
            width=bar_width,
            label=AGENT_LABELS[agent],
            color=AGENT_COLORS[agent],
        )
        if len(fact_limits) <= 8:
            annotate_bars_vertical(ax, bars)

    ax.set_title(
        f"Accuracy vs Memory Budget on {pretty_dataset_name(dataset_name)}",
        fontsize=16,
    )
    ax.set_xlabel("Memory Budget (Fact Limit)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 100)
    ax.set_xticks(x_positions)
    ax.set_xticklabels([str(fact_limit) for fact_limit in fact_limits])
    ax.legend(ncols=2, frameon=False)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate one presentation-ready graph from benchmark CSV results."
    )
    parser.add_argument(
        "--output-dir",
        default="results/graphs",
        help="Directory where graph images will be saved.",
    )

    subparsers = parser.add_subparsers(dest="graph_type", required=True)

    hero_parser = subparsers.add_parser(
        "hero", help="Generate one hero chart for a single dataset."
    )
    hero_parser.add_argument("dataset", help="Dataset name, for example mixed_chain_small.")
    hero_parser.add_argument(
        "--benchmark-csv",
        default="results/benchmark.csv",
        help="Path to benchmark.csv output.",
    )

    all_parser = subparsers.add_parser(
        "all-datasets", help="Generate one grouped bar chart across datasets."
    )
    all_parser.add_argument(
        "datasets",
        nargs="*",
        help="Optional dataset names to include. Leave empty to include every dataset.",
    )
    all_parser.add_argument(
        "--benchmark-csv",
        default="results/benchmark.csv",
        help="Path to benchmark.csv output.",
    )

    tradeoff_parser = subparsers.add_parser(
        "tradeoff", help="Generate one memory tradeoff chart for a single dataset."
    )
    tradeoff_parser.add_argument(
        "dataset", help="Dataset name, for example greater_chain_large."
    )
    tradeoff_parser.add_argument(
        "--sweep-csv",
        default="results/mem_limit_sweep.csv",
        help="Path to mem_limit_sweep.csv output.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.graph_type == "hero":
        benchmark_rows = load_csv_rows(Path(args.benchmark_csv))
        require_dataset(benchmark_rows, args.dataset, "benchmark CSV")
        output_path = output_dir / timestamped_filename(f"hero_{args.dataset}", timestamp)
        plot_hero_chart(benchmark_rows, args.dataset, output_path)
    elif args.graph_type == "all-datasets":
        benchmark_rows = load_csv_rows(Path(args.benchmark_csv))
        if args.datasets:
            output_path = output_dir / timestamped_filename(
                f"all_datasets_grouped_{slugify_dataset_list(args.datasets)}",
                timestamp,
            )
        else:
            output_path = output_dir / timestamped_filename("all_datasets_grouped", timestamp)
        plot_all_datasets_grouped(benchmark_rows, output_path, args.datasets)
    elif args.graph_type == "tradeoff":
        sweep_rows = dedupe_rows(
            load_csv_rows(Path(args.sweep_csv)),
            ("dataset", "agent", "fact_limit"),
        )
        require_dataset(sweep_rows, args.dataset, "memory sweep CSV")
        output_path = output_dir / timestamped_filename(
            f"memory_tradeoff_{args.dataset}",
            timestamp,
        )
        plot_memory_tradeoff(sweep_rows, args.dataset, output_path)
    else:  # pragma: no cover - argparse enforces subcommands
        raise ValueError(f"Unsupported graph type: {args.graph_type}")

    print(f"Generated graph: {output_path}")


if __name__ == "__main__":
    main()
