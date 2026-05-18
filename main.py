import argparse
from pathlib import Path
from data import load_stream, load_quiz
from agents import SimpleAgent, RandomAgent
from quiz import run_quiz


FACT_LIMIT = 20 #increase to 40 for better performance tho


def helper_run(agent_name: str, agent, stream, quiz_questions):
    #a helper function to run the quiz for any agent, js call it
    #more convienient
    print(f"{'='*70}")
    print(f"{agent_name} is processing the stream...")
    print(f"{'='*70}")
    
    for fact in stream:
        agent.process(fact)
    
    print("\nAgent memory after stream:")
    agent.show()

    print("\nRunning quiz...")
    score = run_quiz(agent, quiz_questions)
    print(f"Results for {agent_name}: {score}")

    return score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", default="datasets/small", help="path to dataset directory")
    args = parser.parse_args()
    dataset = Path(args.stream)
    stream = load_stream(dataset / "stream.json")
    quiz_questions = load_quiz(dataset / "quiz.json")

    #comparing all the agents
    print(f"Comparing agents on dataset: {dataset.name}\n")
    print(f"Dataset: {dataset}")
    print(f"Stream length: {len(stream)}")
    print(f"Fact limit: {FACT_LIMIT}")
    print(f"Quiz questions: {len(quiz_questions)}\n")

    #simple agent
    print("\n")
    simple_agent = SimpleAgent(fact_limit=FACT_LIMIT)
    simple_score = helper_run("SimpleAgent", simple_agent, stream, quiz_questions)
    
    #random agent
    print("\n")
    random_agent = RandomAgent(fact_limit=FACT_LIMIT)
    random_score = helper_run("RandomAgent", random_agent, stream, quiz_questions)

    #add more agents once we have em


    #comparing
    print(f"\n{'='*70}")
    print(f"\nFinal Scores:")
    print(f"SimpleAgent: {simple_score}")
    print(f"RandomAgent: {random_score}")


if __name__ == "__main__":
    main()
