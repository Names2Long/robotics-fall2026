"""Choose the next handover action from the current phase and event."""


def decide(state, event):
    phase = state["phase"]
    kind = event["kind"]
    target = event["target"]

    active_phases = ("CLARIFY", "CONFIRM", "EXECUTING", "WAIT_READY")
    request_phases = ("IDLE", "CLARIFY", "CONFIRM", "RECOVERY", "CANCELLED")
    named_cup = target in ("red", "blue")

    if kind == "CANCEL" and phase in active_phases:
        return "cancel"

    if kind == "REQUEST" and phase in request_phases:
        if named_cup:
            return "select"
        return "clarify"

    if kind == "CORRECT" and phase in active_phases and named_cup:
        return "select"

    if kind == "CONFIRM" and phase == "CONFIRM":
        return "begin"

    if kind == "TICK" and phase == "EXECUTING":
        return "advance"

    if kind == "READY" and phase == "WAIT_READY":
        return "release"

    if kind == "TIMEOUT" and phase == "WAIT_READY":
        return "timeout"

    return "hold"