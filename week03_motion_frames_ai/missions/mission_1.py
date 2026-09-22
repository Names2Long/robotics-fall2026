from __future__ import annotations
import math
from lab.models import RequirementResult, make_check
from simulation.kinematics import SEQUENCES

REFLECTIONS = ("trial_synthesis", "hallway_analysis")


def valid_run(run, prediction):
    if not run or not prediction or run.get("prediction_id") != prediction.get("id"):
        return False
    if str(run.get("captured_at", "")) < str(prediction.get("saved_at", "~")):
        return False
    if not run.get("completed"):
        return False
    source = run.get("source")
    if source == "live":
        if not (run.get("stop_sent") and run.get("stop_observed")):
            return False
    elif source == "modeled":
        if not run.get("modeled_stop") or not run.get("model_description"):
            return False
    else:
        return False
    try:
        return all(math.isfinite(float(run["observed_pose"][key])) for key in ("x", "y", "theta"))
    except (KeyError, TypeError, ValueError):
        return False


def evaluate(runs, responses):
    predictions = responses.get("mission_1.predictions", {})
    by_name = {run.get("sequence_id"): run for run in runs}
    predicted = sum(bool(predictions.get(name, {}).get("description", "").strip())
                    and bool(predictions.get(name, {}).get("id")) for name in SEQUENCES)
    completed = sum(valid_run(by_name.get(name), predictions.get(name)) for name in SEQUENCES)
    comparisons = sum(bool(str(responses.get(f"mission_1.compare.{name}", "")).strip()) for name in SEQUENCES)
    sketch = bool(responses.get("mission_1.sketch"))
    reflections = all(str(responses.get(f"mission_1.{key}", "")).strip() for key in REFLECTIONS)
    models = sum(run.get("source") == "modeled" for run in runs)
    requirements = [
        RequirementResult("predictions", "Three predictions saved before their trials", predicted==3, predicted, "3"),
        RequirementResult("sketch", "Turn-then-drive prediction sketch saved", sketch, "saved" if sketch else "missing", "saved"),
        RequirementResult("runs", "Three matched live or modeled results", completed==3, completed, "3"),
        RequirementResult("comparisons", "Each trial has a discrepancy explanation", comparisons==3, comparisons, "3"),
        RequirementResult("reflection", "Trial comparison and public-hallway analysis complete", reflections, "complete" if reflections else "unfinished", "complete"),
    ]
    summary = "You compared motion predictions with evidence."
    if models:
        summary += f" {models} trial(s) use modeled evidence; live execution for those trials remains unverified."
    return make_check(summary, requirements)
