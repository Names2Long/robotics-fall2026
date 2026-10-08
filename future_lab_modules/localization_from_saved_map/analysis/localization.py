from __future__ import annotations

import math


def summarize(samples: list[dict], started_at: float = 0.0) -> dict:
    valid = [row for row in samples if all(key in row for key in ("time", "x", "y", "yaw", "covariance_trace"))]
    if not valid: return {"sample_count": 0, "duration": 0.0, "convergence_time": None, "final_covariance": None, "settled_position_spread": None, "pose_jump": None}
    final = valid[-1]; settled = valid[max(0, len(valid) - 20):]
    convergence = next((row["time"] - started_at for row in valid if row["covariance_trace"] <= 0.5), None)
    cx = sum(row["x"] for row in settled) / len(settled); cy = sum(row["y"] for row in settled) / len(settled)
    spread = math.sqrt(sum((row["x"] - cx) ** 2 + (row["y"] - cy) ** 2 for row in settled) / len(settled))
    jumps = [math.hypot(b["x"] - a["x"], b["y"] - a["y"]) for a, b in zip(valid, valid[1:])]
    metrics = {"sample_count": len(valid), "duration": final["time"] - valid[0]["time"], "convergence_time": convergence, "final_covariance": final["covariance_trace"], "settled_position_spread": spread, "pose_jump": max(jumps, default=0.0)}
    referenced = [row for row in valid if all(key in row for key in ("reference_x", "reference_y", "reference_yaw"))]
    if len(referenced) >= max(20, math.ceil(.8 * len(valid))) and referenced[-1] is final:
        errors = [
            (row["time"], math.hypot(row["x"] - row["reference_x"], row["y"] - row["reference_y"]),
             abs(math.atan2(math.sin(row["yaw"] - row["reference_yaw"]), math.cos(row["yaw"] - row["reference_yaw"]))),
             row["covariance_trace"])
            for row in referenced
        ]
        metrics["reference_available"] = True
        metrics["final_position_error"] = errors[-1][1]
        metrics["final_heading_error"] = errors[-1][2]
        metrics["false_confident_samples"] = sum(cov <= .5 and position > .5 for _, position, _, cov in errors)
        metrics["correct_convergence_time"] = next(
            (errors[index + 2][0] - started_at for index in range(len(errors) - 2)
             if all(position <= .30 and heading <= .25 for _, position, heading, _ in errors[index:index + 3])),
            None,
        )
    else:
        metrics.update(reference_available=False, final_position_error=None, final_heading_error=None,
                       false_confident_samples=None, correct_convergence_time=None)
    return metrics


def trial_passes(condition: str, metrics: dict) -> bool:
    try:
        count = int(metrics.get("sample_count", 0))
        duration = float(metrics.get("duration", 0))
        covariance = float(metrics["final_covariance"])
        spread = float(metrics["settled_position_spread"])
        jump = float(metrics["pose_jump"])
        retention = float(metrics.get("scan_retention", 1.0))
        if not all(math.isfinite(value) for value in (duration, covariance, spread, jump, retention)):
            return False
        if count < 20 or duration < 10:
            return False
        # The exercise grades a valid controlled observation, not a prescribed
        # AMCL outcome. A confidently wrong pose is important evidence too.
        if condition in ("good_initial_pose", "incorrect_initial_pose", "ambiguous_location"):
            return True
        if condition == "degraded_sensor": return retention <= .60
        return False
    except (KeyError, ValueError, TypeError, OverflowError):
        return False


def localization_decision(metrics: dict, covariance_limit: float, convergence_limit: float) -> str:
    """A deliberately simple evidence-only rule for students to critique."""
    if metrics.get("sample_count", 0) < 20:
        return "STOP — insufficient pose evidence"
    if metrics.get("scan_retention", 1.0) < .60:
        return "STOP — degraded scan evidence"
    time = metrics.get("convergence_time")
    covariance = metrics.get("final_covariance")
    if time is None or covariance is None or time > convergence_limit or covariance > covariance_limit:
        return "ASK FOR HELP — localization uncertain"
    return "SLOW — estimate appears concentrated; verify with independent evidence"
