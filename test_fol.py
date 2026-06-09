from pathlib import Path
from data import load_stream, load_quiz
from agents import FOLCompressionAgent
from quiz import run_quiz

# Suggested fact limits (memory and learning trace each sum to fact_limit):
#   greater_chain_small:        20
#   greater_chain_large:        52  (49 chain links + 3 not_greater)
#   divisibility_chain_small:   10
#   divisibility_chain_large:   47  (44 chain links + 3 not_divides)
#   equals_chain_small:         10
#   equals_chain_large:         50
# Greater/divisibility quizzes use all unique transitive pairs + stream negatives.

DATASET = Path("datasets/greater_chain_large")
FACT_LIMIT = 52
SHOW_UNKNOWNS = True

stream = load_stream(DATASET / "stream.json")
quiz = load_quiz(DATASET / "quiz.json")

agent = FOLCompressionAgent(fact_limit=FACT_LIMIT)

for fact in stream:
    agent.process(fact)

agent.finalize()

print("\n=== After stream ===")
agent.show()

score = run_quiz(agent, quiz, show_unknowns=SHOW_UNKNOWNS)
print(f"\nQuiz: {score}")
