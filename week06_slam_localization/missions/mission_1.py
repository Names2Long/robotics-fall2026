from lab.models import RequirementResult, make_check
import math
REFLECTIONS = ("limitations", "drift_and_revisit")


def _number(value, default=0):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def evaluate(evidence, responses, has_yaml, has_image):
    req = [
        RequirementResult("files", "Matching map YAML, PGM, and analysis supplied", has_yaml and has_image, f"YAML={has_yaml}, image={has_image}", "validated pair"),
    ]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_1.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 100, len(text), "≥ 100 characters"))
    plan = str(responses.get("mission_1.route.original_prediction", "")).strip()
    req.append(RequirementResult("route", "Route plan saved before mapping", len(plan) >= 40, len(plan), "≥ 40 characters"))
    return make_check("Mission 1 includes a saved map and an evidence-based explanation.", req)
