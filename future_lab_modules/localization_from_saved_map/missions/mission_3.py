from analysis.localization import trial_passes
from lab.models import RequirementResult, make_check
CONDITIONS = ("good_initial_pose", "incorrect_initial_pose", "ambiguous_location", "degraded_sensor")
REFLECTIONS = ("knowing_where", "recovery", "sensor_effect", "deployment_limit")
def evaluate(trials, responses):
    req = []
    for condition in CONDITIONS:
        evidence = trials.get(condition, {}); metrics = evidence.get("metrics", {})
        req.append(RequirementResult(condition, condition.replace("_", " ").title(), trial_passes(condition, metrics), metrics or "missing", "condition criteria"))
    good = trials.get("good_initial_pose", {}).get("metrics", {}); degraded = trials.get("degraded_sensor", {}).get("metrics", {})
    comparison = trial_passes("good_initial_pose", good) and trial_passes("degraded_sensor", degraded)
    req.append(RequirementResult("degradation", "Normal/degraded comparison is measurable", comparison, f"good covariance={good.get('final_covariance')}, degraded covariance={degraded.get('final_covariance')}, retention={degraded.get('scan_retention')}", "both uncertainties plus ≤60% retention"))
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_3.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 120, len(text), "≥ 120 characters"))
    for condition in CONDITIONS:
        prediction = str(responses.get(f"mission_3.{condition}.original_prediction", "")).strip()
        observation = str(responses.get(f"mission_3.{condition}.observation", "")).strip()
        correctness = str(responses.get(f"mission_3.{condition}.correctness", "Choose…"))
        req.append(RequirementResult(condition + "_prediction", "Prediction before " + condition.replace("_", " "), len(prediction) >= 30, len(prediction), "≥ 30 characters"))
        req.append(RequirementResult(condition + "_observation", "Observed " + condition.replace("_", " "), len(observation) >= 60, len(observation), "≥ 60 characters"))
        req.append(RequirementResult(condition + "_correctness", "Correctness judgment for " + condition.replace("_", " "), correctness in ("Correct", "Incorrect", "Uncertain"), correctness, "choose one"))
    rule = str(responses.get("mission_3.policy_reasoning", "")).strip()
    req.append(RequirementResult("policy", "Localization decision rule justified", len(rule) >= 120, len(rule), "≥ 120 characters"))
    return make_check("Mission 3 documents localization success, failure, recovery, and limits.", req)
