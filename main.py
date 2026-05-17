import argparse
from pathlib import Path
from data import load_stream, load_quiz
from agents import SimpleAgent
from quiz import run_quiz


FACT_LIMIT = 20


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="datasets/small", help="path to dataset directory")
    args = parser.parse_args()

    dataset = Path(args.dataset)
    stream = load_stream(dataset / "stream.json")
    quiz_questions = load_quiz(dataset / "quiz.json")

    print(f"=== Week 7: Simple Agent (no rules, {FACT_LIMIT}-fact limit) ===")
    print(f"Dataset:              {dataset}")
    print(f"Fact stream length:   {len(stream)}")
    print(f"Agent fact limit:     {FACT_LIMIT}")
    print(f"Quiz questions:       {len(quiz_questions)}\n")

    agent = SimpleAgent(fact_limit=FACT_LIMIT)

    print("Feeding stream...")
    for fact in stream:
        agent.process_fact(fact)

    print("\nAgent memory after stream:")
    agent.show()

    print("\nRunning quiz...")
    result = run_quiz(agent, quiz_questions)
    print(f"Result: {result}")
    print(
        "\nNote: this agent can only confirm facts it currently stores. "
        "Unknown = fact was evicted or never seen."
    )


if __name__ == "__main__":
    main()
