"""Current paired potential-field experiment contract."""
from evaluation.experiments import social_checks
REFLECTIONS = ("prediction", "comparison", "recommendation")

def evaluate(evidence):
    return social_checks((evidence or {}).get("rows", []))

