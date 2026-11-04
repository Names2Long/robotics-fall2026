"""Current offline-search evidence contract."""
from evaluation.experiments import offline_checks
REFLECTIONS = ("search", "failure")

def evaluate(evidence):
    return offline_checks(evidence or {})

