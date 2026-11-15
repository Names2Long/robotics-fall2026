"""Complete decide() using the transition requirements in the Lab 10 guide."""


def decide(state, event):
    phase = state["phase"]
    kind = event["kind"]
    target = event["target"]

    if kind == "CANCEL":
        return "hold"  # TODO Mission 1. Cancel before processing active work.

    if kind in ("REQUEST", "CORRECT"):
        return "select"  # TODO Mission 1. Clarify an unnamed target and guard when a request may replace it.

    if kind == "CONFIRM" and phase == "CONFIRM":
        return "begin"

    if phase == "WAIT_READY":
        return "release"  # TODO Tutorial. Require the READY event too.

    if kind == "TIMEOUT":
        return "hold"  # TODO Mission 1. Enter recovery from a waiting state.

    if kind == "TICK" and phase == "EXECUTING":
        return "advance"

    return "hold"
