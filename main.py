import argparse
from pathlib import Path
import time
from data import load_stream, load_quiz
from agents import SimpleAgent, RandomAgent, ImportanceAgent, FOLCompressionAgent
from quiz import run_quiz


FACT_LIMIT = 20     # increase to 40 for better performance tho
                    # 100 for better perf with large datasets

def helper_run(agent_name: str, agent, stream, quiz_questions, show_unknowns: bool = False):
    # a helper function to run the quiz for any agent, js call it
    # more convenient
    print(f"{'='*70}")
    print(f"{agent_name} is processing the stream...")
    print(f"{'='*70}")
    
    # timing ts
    start_time = time.perf_counter()
    for fact in stream:
        agent.process(fact)
    if hasattr(agent, "finalize"):
        agent.finalize()
    stream_time = time.perf_counter() - start_time
    
    print("\nAgent memory after stream:")
    agent.show()

    start_time_quiz = time.perf_counter()
    score = run_quiz(agent, quiz_questions, show_unknowns=show_unknowns)
    quiz_time = time.perf_counter() - start_time_quiz

    print("\nRunning quiz...")
    print(f"Results for {agent_name}: {score}")
    print(f"Streaming time: {stream_time: .5f} seconds")
    print(f"Quiz time: {quiz_time: .5f} seconds")

    return score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", default="datasets/small", help="path to dataset directory")
    parser.add_argument(
        "--show-unknowns",
        action="store_true",
        help="print quiz questions the agent answered Unknown",
    )
    args = parser.parse_args()
    dataset = Path(args.stream)
    stream = load_stream(dataset / "stream.json")
    quiz_questions = load_quiz(dataset / "quiz.json")

    # comparing all the agents
    print(f"Comparing agents on dataset: {dataset.name}\n")
    print(f"Dataset: {dataset}")
    print(f"Stream length: {len(stream)}")
    print(f"Fact limit: {FACT_LIMIT}")
    print(f"Quiz questions: {len(quiz_questions)}\n")

    # simple agent
    print("\n")
    simple_agent = SimpleAgent(fact_limit=FACT_LIMIT)
    simple_score = helper_run("SimpleAgent", simple_agent, stream, quiz_questions, args.show_unknowns)
    
    # random agent
    print("\n")
    random_agent = RandomAgent(fact_limit=FACT_LIMIT)
    random_score = helper_run("RandomAgent", random_agent, stream, quiz_questions, args.show_unknowns)

    # Importance agent
    print("\n")
    importance_agent = ImportanceAgent(fact_limit=FACT_LIMIT)
    importance_score = helper_run("ImportanceAgent", importance_agent, stream, quiz_questions, args.show_unknowns)

    # FOL agent
    print("\n")
    fol_agent = FOLCompressionAgent(fact_limit=FACT_LIMIT)
    fol_score = helper_run("FOLCompressionAgent", fol_agent, stream, quiz_questions, args.show_unknowns)

    # comparing
    print(f"\n{'='*70}")
    print(f"\nFinal Scores: ")
    print(f"SimpleAgent: {simple_score}")
    print(f"RandomAgent: {random_score}")
    print(f"ImportanceAgent: {importance_score}")
    print(f"FOLCompressionAgent: {fol_score}")


if __name__ == "__main__":
    main()
