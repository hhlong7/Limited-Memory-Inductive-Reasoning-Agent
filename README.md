# Limited Memory Inductive Reasoning Agent

**Team:** Christian Moran, Yasmin Akkaya, Long, Dennis Kulik  
**Course:** CSC 480

---

## Goal

Build an agent that receives a stream of facts, has a fixed memory limit, and must decide what to remember, what to forget, and when to generalize repeated observations into first-order logic rules — so it can answer future queries accurately despite not having seen every fact.

---

## The Core Claim

> A **FOL Compression Agent** answers more queries correctly than naive limited-memory agents because it replaces repeated facts with general, reusable rules.

---

## Agent Types

All agents share the same memory limit for a fair comparison.

| Agent | File | Strategy |
|---|---|---|
| **Simple / Recent** | `agents/simple.py` | Keeps the N most recently seen facts, no rules |
| **Random** | `agents/random.py` | Randomly selects which facts to keep *(Week 8)* |
| **Importance** | `agents/importance.py` | Keeps facts ranked by a heuristic score, no compression *(Week 8)* |
| **FOL Compression** *(ours)* | `agents/fol.py` | Generalizes repeated patterns into FOL rules to compress knowledge *(Week 8+)* |

---

## Project Structure

```
.
├── facts.py              # Fact, Rule dataclasses
├── logic.py              # LogicMemory, fact_to_z3, rule_to_z3
├── data.py               # Fact stream + quiz generation, load/save
├── quiz.py               # QuizResult, run_quiz
├── main.py               # Entry point
├── generate_dataset.py   # One-time script to write dataset files
├── agents/
│   ├── __init__.py       # Re-exports all agent classes
│   ├── base.py           # BaseAgent abstract interface
│   └── simple.py         # SimpleAgent (Week 7 baseline)
├── datasets/
│   ├── small/            # max_n=10, 45 facts, 30 quiz questions
│   │   ├── stream.json
│   │   └── quiz.json
│   └── large/            # max_n=15, 105 facts, 50 quiz questions
│       ├── stream.json
│       └── quiz.json
├── pyproject.toml        # uv project config
└── uv.lock               # Locked dependency versions
```

### `facts.py`
- `Fact(predicate, args)` — immutable dataclass for a single FOL fact, e.g. `greater(5, 3)`
- `Rule(premises, conclusion, name)` — immutable dataclass for an FOL rule

### `logic.py`
- `fact_to_z3(fact)` / `rule_to_z3(rule)` — convert to Z3 boolean expressions
- `LogicMemory(fact_limit, rule_limit)` — bounded storage with FIFO eviction; uses Z3 to answer queries as `"True"`, `"False"`, or `"Unknown"`

### `agents/`
- `base.py` — `BaseAgent`: abstract interface with `process_fact(fact)` and `answer_query(fact) -> str`
- `simple.py` — `SimpleAgent`: wraps `LogicMemory` with `rule_limit=0`; FIFO eviction; Week 7 baseline

### `data.py`
- `generate_greater_stream(max_n, seed)` — all true `greater(i, j)` facts for integers 1..N, shuffled
- `generate_quiz(max_n, n_questions, seed)` — quiz questions with expected answer `"True"`; measures recall
- `save_stream` / `save_quiz` / `load_stream` / `load_quiz` — serialize to/from JSON

### `quiz.py`
- `QuizResult` — holds `total`, `correct`, `unknown_count` with `accuracy` and `answer_rate` properties
- `run_quiz(agent, questions)` — feeds questions to any agent and returns a `QuizResult`

### `datasets/`
Fixed JSON files generated once by `generate_dataset.py`. All agents load from the same files to guarantee a fair comparison. Do not regenerate unless intentionally changing the benchmark.

---

## How to Run

### 1. Install dependencies

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

### 2. Run an experiment

```bash
# default: datasets/small
uv run python main.py

# larger dataset
uv run python main.py --dataset datasets/large
```

**Example output (small dataset):**

```
=== Week 7: Simple Agent (no rules, 20-fact limit) ===
Dataset:              datasets/small
Fact stream length:   45
Agent fact limit:     20
Quiz questions:       30

Feeding stream...

Agent memory after stream:
Facts:
  greater(10, 6) {'score': 0.0}
  ...

Running quiz...
Result: Correct: 13/30 (43.3%) | Answered: 13/30 (43.3%) | Unknown: 17

Note: this agent can only confirm facts it currently stores.
Unknown = fact was evicted or never seen.
```

The simple agent stores only the 20 most recently seen facts. Any earlier fact gets evicted, so the agent answers `"Unknown"` for those — this low recall score is the baseline we aim to beat with the FOL Compression Agent.

### 3. Regenerate datasets (intentional only)

```bash
uv run python generate_dataset.py
```

This overwrites `datasets/`. Only do this if changing benchmark parameters.

---

## Design Decisions

### Memory Model
- Separate bounded stores for facts and rules (`fact_limit`, `rule_limit`)
- FIFO eviction: oldest item removed when capacity is reached
- All reasoning delegated to Z3: facts and rules are asserted as boolean constraints, queries checked via entailment

### Query Answering (Z3)
For a query `Q`:
1. Assert `NOT Q` — if `unsat`, then `Q` must be true → return `"True"`
2. Assert `Q` — if `unsat`, then `Q` contradicts memory → return `"False"`
3. Otherwise → `"Unknown"`

### Fixed Datasets
Quiz questions and fact stream ordering are saved to JSON once. All agents load from the same files so that accuracy scores are directly comparable — no risk of silent benchmark drift if generation logic changes.

### Compression Trigger (Planned — Week 8+)
Hybrid approach:
- **Frequency threshold** fires compression candidates (simple trigger)
- **Utility score** picks which candidate to generalize first (quality filter)

### Scoring Functions (Planned)
- **Fact utility:** number of times referenced by rules (less referenced = more valuable to keep)
- **Rule utility:** how many facts it explains, whether it causes contradictions, domain coverage

---

## Tech Stack

| Layer | Tool |
|---|---|
| Core logic | Python 3.11+ |
| Formal reasoning | [z3-solver](https://pypi.org/project/z3-solver/) 4.13.4.0 |
| Inductive learning | ILP (planned — Week 8+) |
| Dependency management | [uv](https://docs.astral.sh/uv/) |

---

## Roadmap

| Milestone | Date | Goal |
|---|---|---|
| **Check-in 1** | May 14 | Data pipeline, Z3 baseline, `SimpleAgent`, quizzes |
| **Check-in 2** | May 28 | All baseline agents + FOL Compression Agent |
| **Presentation** | Jun 11 | Full benchmarks, analysis, write-up |

### Week 7 ✅
- [x] `Fact` / `Rule` dataclasses (`facts.py`)
- [x] Z3 translation + query answering (`logic.py`)
- [x] `LogicMemory` with bounded storage and FIFO eviction
- [x] Fixed math comparison datasets (`datasets/small`, `datasets/large`)
- [x] Quiz system with accuracy + answer-rate scoring (`quiz.py`)
- [x] `SimpleAgent` baseline — no rules, 20-fact limit (`agents/simple.py`)

### Week 8
- [ ] `RandomAgent` — random eviction policy (`agents/random.py`)
- [ ] `ImportanceAgent` — heuristic-based eviction, no compression (`agents/importance.py`)
- [ ] `FOLCompressionAgent` — detects patterns, generalizes into rules (`agents/fol.py`)
- [ ] Expanded dataset (divisibility, transitivity chains)

### Week 9
- [ ] Full benchmarks across all agents on both datasets
- [ ] Vary memory limits and measure accuracy curves
- [ ] Compare against an unconstrained agent
