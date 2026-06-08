from pathlib import Path
from data import load_stream, load_quiz
from agents import FOLCompressionAgent
from quiz import run_quiz

# Suggested fact limits (need all chain links in memory for 100% on transitive quiz):
#   greater_chain_small:        20
#   greater_chain_large:        49
#   divisibility_chain_small:   10
#   divisibility_chain_large:   44

DATASET = Path("datasets/divisibility_chain_small")
FACT_LIMIT = 10

stream = load_stream(DATASET / "stream.json")
quiz = load_quiz(DATASET / "quiz.json")

agent = FOLCompressionAgent(fact_limit=FACT_LIMIT)

for fact in stream:
    agent.process(fact)

agent.finalize()

print("\n=== After stream ===")
agent.show()

score = run_quiz(agent, quiz)
print(f"\nQuiz: {score}")
