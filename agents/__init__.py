# TODO: FOLCompressionAgent (agents/fol.py) needs a pattern detection mechanism —
# something that watches stored facts, identifies recurring structural patterns
# (e.g. repeated pairs that suggest transitivity), and generalizes them into rules.
# This is essentially a mini ILP engine and is the core of the project.

from agents.base import BaseAgent
from agents.simple import SimpleAgent
from agents.random import RandomAgent

__all__ = ["BaseAgent", "SimpleAgent", "RandomAgent"]
