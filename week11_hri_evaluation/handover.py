"""Deterministic cup simulator and event replay shared by all three modes."""
from copy import deepcopy
import time

CUPS = {"red": 3, "blue": 5}
CHECKPOINT = 2
MODES = ("Manual teleoperation", "Shared autonomy with voice", "Autonomous execution")
ACTIVE = {"CLARIFY", "CONFIRM", "EXECUTING", "WAIT_READY"}
TERMINAL = {"COMPLETE", "CANCELLED", "RECOVERY"}
FEEDBACK = {
    "IDLE": "Waiting for your request.",
    "CLARIFY": "Which cup do you mean, red or blue?",
    "CONFIRM": "I understood {target}. Say confirm or correct the cup.",
    "EXECUTING": "Retrieving the {target} cup. You can cancel.",
    "WAIT_READY": "Offering the {target} cup. Signal Ready to receive it.",
    "COMPLETE": "Handover complete.",
    "CANCELLED": "Cancelled. The robot has stopped.",
    "RECOVERY": "Timed out. The robot has stopped. Start a new request.",
}
PHRASES = {
    "bring me the blue cup": ("REQUEST", "blue"),
    "bring me the red cup": ("REQUEST", "red"),
    "bring me the cup": ("REQUEST", None),
    "the blue cup": ("REQUEST", "blue"),
    "the red cup": ("REQUEST", "red"),
    "blue cup": ("REQUEST", "blue"),
    "red cup": ("REQUEST", "red"),
    "actually bring me the red cup": ("CORRECT", "red"),
    "actually bring me the blue cup": ("CORRECT", "blue"),
    "correct to red cup": ("CORRECT", "red"),
    "correct to blue cup": ("CORRECT", "blue"),
    "confirm": ("CONFIRM", None),
    "yes": ("CONFIRM", None),
    "ready": ("READY", None),
    "not ready": ("WAIT", None),
    "i am not ready": ("WAIT", None),
    "no i am not ready": ("WAIT", None),
    "wait": ("WAIT", None),
    "can you wait": ("WAIT", None),
    "please hold on": ("WAIT", None),
    "do not confirm": ("WAIT", None),
    "do not release the cup": ("WAIT", None),
    "no": ("WAIT", None),
    "cancel": ("CANCEL", None),
    "stop": ("CANCEL", None),
}


def interpret(transcript):
    text = " ".join(transcript.lower().strip(" .?!").split())
    kind, target = PHRASES.get(text, ("UNRECOGNIZED", None))
    return event(kind, target)


def event(kind, target=None):
    return {"kind": kind, "target": target}


def initial(mode=MODES[1], scenario="normal"):
    manual = mode == MODES[0]
    return {
        "mode": mode, "scenario": scenario, "phase": "EXECUTING" if manual else "IDLE",
        "position": 0, "target": "blue" if manual else None, "held": None, "delivered": None,
        "confirmed": manual, "checkpoint_seen": False, "waiting_for_change": False,
    }


def status(state, redesign=None):
    if state["waiting_for_change"]:
        return "Paused at the marked checkpoint. Give the correction or cancel as directed."
    messages = dict(FEEDBACK)
    if redesign:
        messages[redesign["phase"]] = redesign["message"]
    return messages[state["phase"]].replace("{target}", state["target"] or "the selected cup")


def move(state, direction):
    state["position"] = max(0, min(5, state["position"] + direction))


def checkpoint(state):
    if (state["scenario"] in ("correction", "cancel", "changed")
            and not state["checkpoint_seen"] and state["position"] == CHECKPOINT
            and state["target"] == "blue" and not state["held"]):
        state.update(checkpoint_seen=True, waiting_for_change=True)


def advance(state):
    """One supplied movement, pickup, or offer step."""
    if state["phase"] != "EXECUTING" or state["waiting_for_change"]:
        return
    target = state["target"]
    if target not in CUPS:
        return
    destination = 0 if state["held"] else CUPS[target]
    if destination != state["position"]:
        move(state, 1 if destination > state["position"] else -1)
        checkpoint(state)
    elif state["held"]:
        state["phase"] = "WAIT_READY"
    else:
        state["held"] = target


def step(state, incoming, decide=None):
    """Apply one event and report the decision. Student rules run only in shared mode."""
    after = deepcopy(state)
    kind, target = incoming["kind"], incoming.get("target")
    phase = after["phase"]
    decision = "hold"
    if kind == "STOP":
        decision = "cancel" if phase != "COMPLETE" else "hold"
    elif kind == "UNRECOGNIZED":
        decision = "repeat"
    elif kind == "WAIT":
        decision = "wait"
    elif kind == "REVIEW":
        decision = "review"
    elif after["mode"] == MODES[1]:
        decision = decide(deepcopy(state), dict(incoming))
    elif kind == "READY" and phase == "WAIT_READY":
        decision = "release"
    elif kind == "TIMEOUT" and phase == "WAIT_READY":
        decision = "timeout"
    elif after["mode"] == MODES[0]:
        if kind == "SET_GOAL" and target in CUPS and after["held"] in (None, target) and phase in ("EXECUTING", "CANCELLED", "RECOVERY"):
            after.update(phase="EXECUTING", target=target, confirmed=True, waiting_for_change=False)
            decision = "set_goal"
        elif phase == "EXECUTING" and not after["waiting_for_change"]:
            if kind in ("LEFT", "RIGHT"):
                move(after, -1 if kind == "LEFT" else 1)
                checkpoint(after)
                decision = "move"
            elif kind == "PICK" and not after["held"] and target in CUPS and after["position"] == CUPS[target]:
                after["held"] = target
                decision = "pick"
            elif kind == "OFFER" and after["position"] == 0 and after["held"]:
                after["phase"] = "WAIT_READY"
                decision = "offer"
    elif kind == "START" and target in CUPS and phase in ("IDLE", "CANCELLED", "RECOVERY"):
        if after["held"] != target:
            after["held"] = None
        after.update(phase="EXECUTING", target=target, confirmed=True, waiting_for_change=False)
        decision = "start"
    elif kind == "TICK":
        decision = "advance"

    if decision in ("cancel", "timeout"):
        after.update(phase="CANCELLED" if decision == "cancel" else "RECOVERY",
                     waiting_for_change=False, confirmed=False)
    elif decision in ("select", "clarify"):
        chosen = (target or "blue") if decision == "select" else None
        # A changed request returns any held cup to its original station in this simulator.
        after.update(phase="CONFIRM" if chosen else "CLARIFY", target=chosen, held=None,
                     waiting_for_change=False, confirmed=False)
    elif decision == "begin" and after["target"] in CUPS:
        after.update(phase="EXECUTING", confirmed=True)
    elif decision == "advance":
        advance(after)
    elif decision == "release" and after["held"]:
        after.update(phase="COMPLETE", delivered=after["held"], held=None)
    return after, decision


def new_trial(mode=MODES[1], scenario="normal", redesign=None):
    now = time.time()
    return {
        "state": initial(mode, scenario), "events": [], "start": None, "finished": None,
        "opened": now, "entered": now, "redesign": redesign,
    }


def dispatch(trial, incoming, decide=None, *, source="simulation", intended="", transcript="", now=None):
    now = time.time() if now is None else now
    before = trial["state"]
    after, decision = step(before, incoming, decide)
    if source != "simulation" and trial["start"] is None:
        trial["start"] = now
    if before["phase"] != after["phase"]:
        trial["entered"] = now
    if after["phase"] == "COMPLETE":
        trial["finished"] = trial["finished"] or now
    trial["state"] = after
    if before != after or source != "simulation" or incoming["kind"] != "TICK":
        feedback = status(after, trial["redesign"])
        if decision == "repeat":
            feedback = "Command unclear. Try again or use the typed input."
        elif decision == "wait":
            feedback = "Acknowledged. No permission was given. " + feedback
        elif decision == "review":
            feedback = "Review the recognized permission before applying it. " + feedback
        trial["events"].append({
            "seconds": round(max(0, now - (trial["start"] if trial["start"] is not None else now)), 2),
            "source": source, "intended": intended, "transcript": transcript,
            "event": incoming["kind"], "target": incoming.get("target"), "decision": decision,
            "before": before, "after": after, "feedback": feedback,
        })


def finish(trial):
    data = deepcopy(trial)
    data["finished"] = data["finished"] or time.time()
    state = data["state"]
    expected = "red" if state["scenario"] in ("changed", "correction") else "blue"
    data["outcome"] = (
        "Cancelled" if state["phase"] == "CANCELLED" else
        "Unexpected transfer" if state["scenario"] == "cancel" and state["delivered"] else
        "Correct cup handed over" if state["delivered"] == expected else
        "Wrong cup handed over" if state["delivered"] else "Incomplete handover"
    )
    data["elapsed"] = round(max(0, data["finished"] - (data.get("opened") or data["start"] or data["finished"])), 1)
    data["controller_elapsed"] = round(max(0, data["finished"] - (data["start"] or data["finished"])), 1)
    data["inputs"] = sum(row["source"] != "simulation" for row in data["events"])
    return data


def load_controller(source, filename="controller.py"):
    namespace = {"__name__": "student_controller"}
    exec(compile(source, filename, "exec"), namespace)
    decide = namespace.get("decide")
    if not callable(decide):
        raise ValueError("Define the decide(state, event) function in your controller.")
    return decide


def replay(events, decide):
    trial = new_trial()
    for index, incoming in enumerate(events):
        dispatch(trial, incoming, decide, source="script", now=index)
    return trial


CHECK_GROUPS = ("Select and confirm", "Offer and release", "Interrupt and recover")


def scripted_checks(decide, group=None):
    request = event("REQUEST", "blue")
    confirm = event("CONFIRM")
    ticks = [event("TICK")] * 12
    offer = [request, confirm, *ticks]
    selected = {"phase": "CONFIRM", "target": "blue", "position": 0, "confirmed": False}
    moving = {"phase": "EXECUTING", "confirmed": True, "delivered": None}
    offered = {"phase": "WAIT_READY", "held": "blue", "delivered": None}
    cancelled = {"phase": "CANCELLED", "delivered": None, "confirmed": False}
    corrected = {"phase": "CONFIRM", "target": "red", "position": 1, "confirmed": False}
    ambiguous = {"phase": "CLARIFY", "target": None, "position": 0}
    cases = {
        CHECK_GROUPS[0]: [
            ("Confirmation required", [request, *ticks], [(0, selected), (-1, selected)]),
            ("Clarification before action", [event("REQUEST"), confirm, *ticks],
             [(0, ambiguous), (1, ambiguous), (-1, ambiguous)]),
            ("Resolve ambiguity", [event("REQUEST"), request, confirm], [(0, ambiguous), (1, selected), (2, moving)]),
            ("Refusal leaves confirmation pending", [request, event("WAIT"), event("TICK")],
             [(0, selected), (1, selected), (2, selected)]),
        ],
        CHECK_GROUPS[1]: [
            ("Normal transfer", [*offer, event("READY")],
             [(0, selected), (1, moving), (13, offered), (-1, {"phase": "COMPLETE", "delivered": "blue"})]),
            ("Early and missing readiness", [request, confirm, event("READY"), *ticks, event("TICK")],
             [(0, selected), (1, moving), (2, moving), (14, offered), (-1, offered)]),
            ("Refusal keeps the cup held", [*offer, event("WAIT"), event("TICK")],
             [(13, offered), (14, offered), (-1, offered)]),
        ],
        CHECK_GROUPS[2]: [
            ("Cancel while moving", [request, confirm, event("TICK"), event("CANCEL"), *ticks],
             [(0, selected), (1, moving), (3, cancelled), (-1, {**cancelled, "position": 1})]),
            ("Cancel while offering", [*offer, event("CANCEL"), event("READY")],
             [(13, offered), (14, cancelled), (-1, cancelled)]),
            ("Active task needs an explicit correction", [request, confirm, event("TICK"), event("REQUEST", "red")],
             [(0, selected), (1, moving), (-1, {**moving, "target": "blue"})]),
            ("Missing readiness times out", [*offer, event("TIMEOUT"), event("READY")],
             [(13, offered), (14, {"phase": "RECOVERY", "delivered": None}), (-1, {"phase": "RECOVERY", "delivered": None})]),
            ("Changed goal clears confirmation", [request, confirm, event("TICK"), event("CORRECT", "red"), *ticks],
             [(0, selected), (1, moving), (3, corrected), (-1, corrected)]),
            ("Confirm the corrected goal", [request, confirm, event("TICK"), event("CORRECT", "red"), confirm, *ticks, event("READY")],
             [(3, corrected), (4, moving), (-1, {"phase": "COMPLETE", "delivered": "red"})]),
        ],
    }
    results = []
    for section in (CHECK_GROUPS if group is None else (group,)):
        for name, events, expected in cases[section]:
            trial = replay(events, decide)
            mismatch = None
            for index, fields in expected:
                row = trial["events"][index]
                actual = {key: row["after"][key] for key in fields}
                if actual != fields:
                    mismatch = {"event": row["event"], "before": row["before"]["phase"],
                                "step": index + 1 if index >= 0 else len(events),
                                "expected": fields, "observed": actual}
                    break
            results.append({"case": name, "group": section, "passed": mismatch is None,
                            "first_mismatch": mismatch, "final_state": trial["state"], "trace": trial["events"]})
    return results
