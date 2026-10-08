from lab.models import RequirementResult, make_check
from missions.mission_1 import _number
REFLECTIONS = ("comparison", "map_choice")
def evaluate(first, second, responses):
    m1 = (first or {}).get("metrics", {}); m2 = (second or {}).get("metrics", {})
    strategies = {(first or {}).get("strategy"), (second or {}).get("strategy")}
    req = [
        RequirementResult("runs", "Two valid analyzed maps", bool(m1) and bool(m2), len([x for x in (m1, m2) if x]), "2"),
        RequirementResult("strategies", "Different exploration strategies", len(strategies - {None, ""}) == 2, sorted(x for x in strategies if x), "2 different strategies"),
    ]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_2.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 120, len(text), "≥ 120 characters"))
    prediction = str(responses.get("mission_2.strategy.original_prediction", "")).strip()
    req.append(RequirementResult("prediction", "Strategy prediction saved before run", len(prediction) >= 40, len(prediction), "≥ 40 characters"))
    duration_1 = _number((first or {}).get("duration_minutes"))
    duration_2 = _number((second or {}).get("duration_minutes"))
    req.append(RequirementResult("duration", "Both mapping durations recorded", min(duration_1, duration_2) > 0, (duration_1, duration_2), "positive minutes for each run"))
    return make_check("Mission 2 compares two routes in the same world using map quality and time evidence.", req)
