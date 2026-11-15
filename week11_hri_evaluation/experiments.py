"""Live voice trials and matched control-mode experiments."""
import time
from uuid import uuid4

import streamlit as st

from handover import CUPS, MODES, TERMINAL, event, finish, interpret, status
from lab.storage import archive, planner_source, save
from speech import make_decoder, transcribe

VOICE_CASES = {
    "clear": ("Clear request", "Say ‘Bring me the blue cup’. When it repeats the goal, say ‘Confirm’ and review what it heard. At the offer, say ‘Ready’ and review again.",
              event("REQUEST", "blue")),
    "ambiguous": ("Ambiguous request", "Say ‘Bring me the cup’. Inspect the clarification, then say ‘The blue cup’. Confirm and signal Ready.",
                  event("REQUEST")),
    "correction": ("Correction", "Ask for the blue cup and confirm. At the checkpoint say ‘Actually bring me the red cup’. Confirm the change and signal Ready.",
                   event("CORRECT", "red")),
    "cancel": ("Cancellation", "Ask for the blue cup and confirm. At the checkpoint say ‘Cancel’. Inspect what stops and how it is acknowledged.",
               event("CANCEL")),
}
TIMEOUT_S = 45
TICK_S = 0.85
PERMISSIONS = {"CONFIRM": "CONFIRM", "READY": "WAIT_READY"}


def decoder():
    if "lab10_decoder" not in st.session_state:
        st.session_state.lab10_decoder = make_decoder()
    return st.session_state.lab10_decoder


def start(work, group, key, mode, scenario, redesign=None):
    from ros_client import client
    run = {
        "group": group, "key": key, "id": uuid4().hex,
        "last_tick": time.time(), "recording": 0,
        "controller_source": planner_source().read_text(encoding="utf-8-sig"),
    }
    try:
        result = client().command({"kind": "start", "trial_id": run["id"], "mode": mode,
                                   "scenario": scenario, "source": run["controller_source"], "redesign": redesign})
    except (RuntimeError, ImportError) as error:
        st.session_state.lab10_ros_error = str(error)
        return
    run["trial"] = result["trial"]
    work["active"] = run
    save(work)


def recorded_event(row):
    if row["source"] == "voice":
        return interpret(row["transcript"])
    return event(row["event"], row["target"])


def trial_checks(run):
    trial = run["trial"]
    state = trial["state"]
    scenario, mode = state["scenario"], state["mode"]
    rows = trial["events"]

    def spoke(expected, checkpoint=False):
        return any(row["source"] == "voice" and interpret(row["intended"]) == expected
                   and (not checkpoint or row["before"]["waiting_for_change"]) for row in rows)

    checks = []
    if run["group"] == "practice":
        return [("Send a blue-cup request", any(row["event"] == "REQUEST" and row["target"] == "blue" for row in rows)),
                ("Observe robot movement in Gazebo", trial.get("ros", {}).get("distance_m", 0) > .5)]
    if run["group"] in ("voice", "retest"):
        checks.append(("Speak the scenario’s required command",
                       spoke(VOICE_CASES[scenario][2], scenario in ("correction", "cancel"))))
        if scenario == "ambiguous":
            first = next((index for index, row in enumerate(rows) if row["source"] == "voice"
                          and interpret(row["intended"]) == event("REQUEST")), None)
            repaired = first is not None and any(
                incoming["kind"] == "REQUEST" and incoming["target"] in CUPS
                for row in rows[first + 1:] if row["source"] != "simulation"
                for incoming in (interpret(row["intended"]) if row["source"] == "voice" else recorded_event(row),)
            )
            checks.append(("Try naming a cup after the ambiguous request, even if the first transcript was wrong", repaired))
        return checks

    if scenario == "changed":
        checks.append(("Reach the marked checkpoint with the blue goal", state["checkpoint_seen"]))
    if mode == MODES[1]:
        checks.append(("Speak the initial blue-cup request", spoke(event("REQUEST", "blue"))))
        if scenario == "changed":
            checks.append(("Speak the red-cup correction at the checkpoint", spoke(event("CORRECT", "red"), True)))
    elif scenario == "changed":
        expected = "START" if mode == MODES[2] else "SET_GOAL"
        checks.append(("Use this mode’s controls to redirect to red",
                       any(row["event"] == expected and row["target"] == "red" for row in rows)))
    else:
        expected = ("MANUAL",) if mode == MODES[0] else ("START",)
        checks.append(("Use the movement or start controls", any(row["event"] in expected for row in rows)))
    return checks


def can_save(run):
    return not run["trial"].get("ros", {}).get("invalidated") and all(passed for _, passed in trial_checks(run))


def row_view(row):
    recognized = recorded_event(row)
    return {
        "Time (s)": row["seconds"], "Input": row["source"],
        "Intended words": row["intended"], "Transcript": row["transcript"],
        "Recognized event": recognized["kind"], "Recognized target": recognized["target"],
        "Applied event": row["event"], "Decision": row["decision"],
        "Before": row["before"]["phase"], "After": row["after"]["phase"],
        "Position": row["after"]["position"], "Holding": row["after"]["held"],
        "Delivered": row["after"]["delivered"], "Feedback": row["feedback"],
        "ROS pose": row.get("ros_pose"), "Distance (m)": row.get("ros_distance_m"),
    }


def trace_table(trial):
    if trial["events"]:
        st.dataframe([row_view(row) for row in trial["events"]], hide_index=True)


def checklist(checks):
    st.table([{"Requirement": label, "Status": "Ready" if passed else "Still needed"}
              for label, passed in checks])


def interpret_recording(state, phrase, *, common_ready=False):
    """Propose spoken permissions. Only a separate deliberate control can apply them."""
    incoming = interpret(phrase)
    pending = None
    if incoming["kind"] in PERMISSIONS:
        if state["phase"] == PERMISSIONS[incoming["kind"]] and not (
                common_ready and incoming["kind"] == "READY"):
            pending = {"kind": incoming["kind"], "transcript": phrase, "state": state.copy()}
        incoming = event("REVIEW")
    return incoming, pending


@st.fragment(run_every=TICK_S)
def trial_panel(work):
    from ros_client import heartbeat, send as ros_send
    run = work.get("active")
    if run is None:
        return
    try:
        telemetry = heartbeat(run)
    except (RuntimeError, ImportError) as error:
        st.error(str(error))
        if st.button("Archive disconnected trial"):
            archive(work, "Disconnected ROS trial", run)
            del work["active"]
            save(work)
            st.rerun()
        return
    trial = run["trial"]
    prefix = run["id"]
    mode = trial["state"]["mode"]
    scenario = trial["state"]["scenario"]
    phase = trial["state"]["phase"]
    common_ready = run["group"] == "modes"
    st.subheader(f"Active trial · {mode}")
    if run["group"] in ("voice", "retest"):
        st.write(VOICE_CASES[scenario][1])
    elif scenario == "changed":
        st.write("Start with blue. At the marked checkpoint, change the goal to red using this mode's controls.")
    else:
        st.write("Bring the blue cup to the handover point. Signal Ready when it is offered.")
    if telemetry.get("error"):
        st.error(telemetry["error"])
    display = st.container()

    def send(kind, target=None, source="control"):
        run.pop("pending", None)
        try:
            ros_send(run, event(kind, target), source=source)
            save(work)
            st.rerun()
        except RuntimeError as error:
            st.error(str(error))

    stopped = phase in ("COMPLETE", "CANCELLED")
    controls = st.columns(2)
    if controls[0].button("Stop", key=f"{prefix}-stop", disabled=stopped, type="primary"):
        send("STOP")
    if controls[1].button("Ready", key=f"{prefix}-ready", disabled=phase != "WAIT_READY"):
        send("READY")

    pending = run.get("pending")
    if pending and pending["state"] == trial["state"]:
        consequence = "start the task" if pending["kind"] == "CONFIRM" else "release the cup"
        st.warning(f"Heard “{pending['transcript']}”. Apply it only if you meant to {consequence}.")
        approve, decline = st.columns(2)
        if approve.button("Apply recognized permission", key=f"{prefix}-approve"):
            send(pending["kind"], source="approval")
        if decline.button("Keep waiting", key=f"{prefix}-decline"):
            send("WAIT")

    if mode == MODES[1] and run["group"] != "practice":
        with st.form(f"{prefix}-audio-{run['recording']}"):
            intended = st.text_input("Words you intend to say", max_chars=120,
                                     help="Write the phrase you will speak. The recognizer receives only the recording.")
            audio = st.audio_input("Record one command", sample_rate=16000)
            submitted = st.form_submit_button("Send recorded command", disabled=phase == "COMPLETE")
        if submitted:
            if not audio or not intended.strip():
                st.warning("Enter your intended words and record the command before sending.")
            else:
                try:
                    phrase = transcribe(decoder(), audio.getvalue())
                except (ValueError, RuntimeError) as error:
                    st.error(str(error))
                else:
                    incoming, pending = interpret_recording(trial["state"], phrase, common_ready=common_ready)
                    try:
                        ros_send(run, incoming, source="voice", intended=intended.strip(), transcript=phrase)
                        run["pending"] = pending
                        run["recording"] += 1
                        save(work)
                        st.rerun()
                    except RuntimeError as error:
                        st.error(str(error))
        st.caption("Record one phrase, stop recording, then select Send recorded command. Review spoken Confirm or Ready before applying it.")
        with st.expander("Typed recovery and supported phrases"):
            st.write("Bring me the blue cup · Bring me the cup · The blue cup · Confirm · Actually bring me the red cup · Ready · Wait · Cancel")
            st.caption("Use typed recovery if recognition repeatedly misses a command. For correction and cancellation trials, reach the checkpoint, then try the required command aloud.")
            with st.form(f"{prefix}-typed", clear_on_submit=True):
                typed = st.text_input("Type a recovery command", max_chars=120)
                if st.form_submit_button("Send typed command", disabled=phase == "COMPLETE") and typed.strip():
                    incoming = interpret(typed)
                    if common_ready and incoming["kind"] == "READY":
                        st.info("Use the Ready button for the matched comparison.")
                    else:
                        send(incoming["kind"], incoming["target"], source="typed")
    elif run["group"] == "practice":
        st.write("Send the request, confirm it, and watch Gazebo. When the robot returns to the green pad and offers the cup, select Ready. Stop interrupts the task.")
        cols = st.columns(2)
        if cols[0].button("Request blue cup", disabled=phase not in ("IDLE", "CLARIFY", "CONFIRM", "CANCELLED", "RECOVERY")):
            send("REQUEST", "blue")
        if cols[1].button("Confirm blue request", disabled=phase != "CONFIRM"):
            send("CONFIRM")
    elif mode == MODES[0]:
        if scenario == "changed" and (trial["state"]["waiting_for_change"] or (
                phase == "CANCELLED" and trial["state"]["checkpoint_seen"] and not trial["state"]["held"])):
            if st.button("Change goal to red", key=f"{prefix}-redirect"):
                send("SET_GOAL", "red")
        if phase in ("CANCELLED", "RECOVERY"):
            if st.button("Resume manual control", key=f"{prefix}-resume"):
                send("SET_GOAL", trial["state"]["target"])
        st.write("Use W/S/A/D in the teleoperation terminal to drive forward, reverse, or turn. Space stops. Each key press lasts at most 0.35 seconds. Hold the key to keep driving. The guide must remain open.")
        st.code("bash scripts/manual_control.sh", language="bash")
        manual = st.columns(2)
        for column, label, kind in zip(manual, ("Load cup at station", "Offer at person"), ("PICK", "OFFER")):
            if column.button(label, key=f"{prefix}-{kind}", disabled=phase != "EXECUTING" or trial["state"]["waiting_for_change"]):
                target = next((color for color, position in CUPS.items() if position == trial["state"]["position"]), None) if kind == "PICK" else None
                send(kind, target)
        st.caption("Dock within 0.16 m of the selected station to load. Return within 0.16 m of the green pad to offer.")
    else:
        goal = st.radio("Autonomous goal", ("blue", "red"), horizontal=True, key=f"{prefix}-goal")
        if st.button("Run supplied autonomy", key=f"{prefix}-start",
                     disabled=phase not in ("IDLE", "CANCELLED", "RECOVERY")):
            if not trial["state"]["checkpoint_seen"] and goal != "blue":
                st.warning("Start with the blue cup so the comparison begins at the same goal.")
            else:
                send("START", goal)

    now = time.time()
    state = trial["state"]
    if state["phase"] != phase:
        st.rerun()
    with display:
        from visuals import room
        from ros_client import client
        if client().image and time.monotonic()-client().image_received < 3:
            st.image(client().image, caption="Live Gazebo overview from /lab10/world_view", width="stretch")
        room(telemetry["pose"], state)
        st.write(f"**State** {state['phase']} | **Target** {state['target'] or 'Unspecified'} | **Tray** {state['held'] or 'Empty'}")
        st.caption(f"Live /odom pose. x = {telemetry['pose'][0]:.2f} m, y = {telemetry['pose'][1]:.2f} m. Watch the same robot in Gazebo.")
        st.info(status(state, trial["redesign"]))
        if state["phase"] == "WAIT_READY":
            remaining = max(0, int(TIMEOUT_S - (now - trial["entered"])))
            st.caption(f"Offer expires in about {remaining} seconds. Use Ready to release the cup.")
        last_voice = next((row for row in reversed(trial["events"]) if row["source"] == "voice"), None)
        if last_voice:
            st.dataframe([row_view(last_voice)], hide_index=True)
            if last_voice["event"] in ("UNRECOGNIZED", "WAIT"):
                st.info(last_voice["feedback"])
            if common_ready and recorded_event(last_voice)["kind"] == "READY":
                st.info("Use the same Ready button as in the other modes.")
    with st.expander("View this trial’s event trace"):
        trace_table(trial)

    checks = trial_checks(run)
    checklist(checks)
    terminal = state["phase"] in TERMINAL
    if not terminal:
        st.caption("Finish the interaction or select End as unsuccessful and describe where it stopped.")
    ended = False
    note = ""
    if not terminal:
        note = st.text_input("Reason for ending an unsuccessful attempt", key=f"{prefix}-failure",
                             value=run.get("failure_note", ""), max_chars=240)
        if run.get("failure_note", "") != note:
            run["failure_note"] = note
            save(work)
        ended = st.button("End as unsuccessful", key=f"{prefix}-failed",
                          disabled=not (can_save(run) and note.strip()))
    if st.button("Finish and save trial", key=f"{prefix}-save", disabled=not (can_save(run) and terminal)) or ended:
        record = finish(trial)
        if ended:
            record["end_note"] = note.strip()
        if run["group"] == "retest":
            archive(work, "Earlier matched retest", work.get("retest"))
            work["retest"] = record
            work.pop("voice_analysis", None)
            st.session_state.pop("m2-analysis", None)
        elif run["group"] == "practice":
            archive(work, "Earlier ROS controller practice", work.get("practice"))
            work["practice"] = record
            work["practice_source"] = run["controller_source"]
        else:
            if run["group"] == "voice" and work.get("redesign", {}).get("case") == scenario:
                archive(work, "Retest before the baseline changed", work.pop("retest", None))
                work.pop("voice_analysis", None)
                st.session_state.pop("m2-analysis", None)
            records = work.setdefault(run["group"], {})
            archive(work, f"Earlier {run['group']} run {run['key']}", records.get(run["key"]))
            records[run["key"]] = record
        ros_send(run, event("STOP"))
        del work["active"]
        save(work)
        st.rerun()
    if st.button("Archive active trial and start over", key=f"{prefix}-discard"):
        ros_send(run, event("STOP"))
        archive(work, f"Interrupted {run['group']} run {run['key']}", finish(trial))
        del work["active"]
        save(work)
        st.rerun()
    save(work)
    st.caption("The ROS controller stops motion if it loses the guide heartbeat or fresh odometry. Commands, poses, and trial results are saved locally.")


def intervention(trial):
    rows = trial["events"]
    checkpoint = next((i for i, row in enumerate(rows) if row["after"]["waiting_for_change"]), None)
    if checkpoint is None:
        return "Checkpoint not reached" if trial["state"]["scenario"] == "changed" else "Routine run"
    later = rows[checkpoint + 1:]
    actions = [
        row["event"] for row in later
        if row["event"] in ("STOP", "SET_GOAL", "CORRECT", "START")
    ]
    switched = next((row for row in later if row["after"]["target"] == "red"), None)
    resumed = next((row for row in later if row["after"]["target"] == "red" and row["after"]["phase"] == "EXECUTING"), None)
    route = "Blue paused at checkpoint. " + (" → ".join(actions) or "No redirect recorded")
    return f"{route}. Red selected {switched['seconds']:.1f}s." if switched and not resumed else (
        f"{route}. Red task active at {resumed['seconds']:.1f}s." if resumed else f"{route}. Red never became active.")


def summary(label, trial):
    return {
        "Trial": label, "Outcome": trial["outcome"], "Time (s)": trial["elapsed"],
        "Operator inputs": trial["inputs"], "Final goal": trial["state"]["target"] or "Unspecified",
        "Delivered": trial["state"]["delivered"] or "None", "Intervention": intervention(trial),
        "Distance (m)": trial.get("ros", {}).get("distance_m"),
    }


def saved_traces(records):
    for name, trial in records.items():
        with st.expander(f"Saved trace · {name}"):
            if trial["redesign"]:
                st.write(f"Feedback used for {trial['redesign']['phase']} · {trial['redesign']['message']}")
            trace_table(trial)
