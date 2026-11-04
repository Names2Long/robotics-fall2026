"""Current two-map navigation evidence contract."""
from evaluation.experiments import navigation_checks
REFLECTIONS = ("performance", "choice")

def evaluate(evidence, source_hash):
    return navigation_checks((evidence or {}).get("rows", []), source_hash)

