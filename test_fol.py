from pathlib import Path
from data import load_stream, load_quiz
from agents import FOLCompressionAgent
from quiz import run_quiz

DATASET = Path("datasets/divisibility_chain_large")
# FL on large greater than dataset (150 items) (transitivity found)
# 10 - 0/150
# 20 - 1/150
# 30 - 7/150
# 40 - 25/150
# 45 - 39/150
# 49 - 150/150
FACT_LIMIT = 49

stream = load_stream(DATASET / "stream.json")
quiz = load_quiz(DATASET / "quiz.json")

agent = FOLCompressionAgent(fact_limit=FACT_LIMIT)

for fact in stream:
    agent.process(fact)

if hasattr(agent, "finalize"):
    agent.finalize()

print("\n=== After stream ===")
agent.show()

score = run_quiz(agent, quiz)
print(f"\nQuiz: {score}")