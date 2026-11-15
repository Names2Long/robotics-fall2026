"""Four progressive, illustrated interactions before the live ROS missions."""
import streamlit as st

from handover import MODES, dispatch, event, interpret, load_controller, new_trial, scripted_checks, status
from visuals import controller_editor, flow, stations


TITLES = ("From speech to a shared goal", "When may a robot complete a handover?",
          "Repair a readiness rule in the guide", "Who controls the robot?")


def show_trial(demo):
    state = demo["state"]
    stations(state)
    flow(state["phase"])
    st.info(demo["events"][-1]["feedback"] if demo["events"] else status(state))
    cols = st.columns(3)
    cols[0].metric("Selected cup", state["target"] or "Unspecified")
    cols[1].metric("Cup on tray", state["held"] or "None")
    cols[2].metric("Transferred cup", state["delivered"] or "None")
    if demo["events"]:
        st.dataframe([{"Step": index+1, "Event": row["event"], "Decision": row["decision"],
                       "Before": row["before"]["phase"], "After": row["after"]["phase"],
                       "Feedback": row["feedback"]} for index, row in enumerate(demo["events"])],
                     hide_index=True)


def render(index, work):
    st.title(f"Guided activity {index + 1} of 4 · {TITLES[index]}")
    st.caption("These guided diagrams let you inspect one interaction event at a time. In the missions the same decisions control the TurtleBot3 through ROS 2 in Gazebo.")
    if index == 0:
        return intent_activity(work)
    if index == 1:
        return readiness_activity()
    if index == 2:
        return code_activity(work)
    return modes_activity()


def intent_activity(work):
    st.write("A robot needs to establish which object you want before it moves. This activity follows a spoken request through three stages so you can see where misunderstandings arise.")
    stations({"position": 0})
    st.markdown("**1. What did the person say?**")
    st.write("The intended words are the person's goal. The robot only receives recorded audio. A transcript is the recognizer's best text interpretation of that audio, so its words can differ from the person's intention.")
    cases = {
        "Clear request": ("Bring me the blue cup", "bring me the blue cup"),
        "Ambiguous request": ("Bring me the cup", "bring me the cup"),
        "Wrong color heard": ("Bring me the blue cup", "bring me the red cup"),
        "Refusal misheard": ("Do not confirm", "confirm"),
        "Your microphone check": ("Bring me the blue cup", work.get("mic", "")),
    }
    case = st.radio("Choose the example to inspect", list(cases), horizontal=True)
    intended, transcript = cases[case]
    cols = st.columns(2)
    cols[0].info(f"Person intended · {intended}")
    cols[1].info(f"Recognizer produced · {transcript}")
    st.markdown("**2. What does the controller infer?**")
    parsed = interpret(transcript)
    st.write("The parser turns the transcript into an event, a structured message with a kind and an optional target. REQUEST names a new task. CONFIRM supplies permission. A missing target means the robot has not established which cup to bring.")
    st.json(parsed)
    st.markdown("**3. What should happen next?**")
    if parsed["kind"] == "REQUEST" and parsed["target"]:
        st.success(f"The display should say that it selected {parsed['target']}. The person checks that selection before giving permission.")
        flow("CONFIRM")
    elif parsed["kind"] == "REQUEST":
        st.warning("Both red and blue match the request. The robot asks which cup and waits. Naming blue repairs the missing information.")
        flow("CLARIFY")
    elif parsed["kind"] in ("CONFIRM", "READY"):
        st.warning("A recognizer can mistake a refusal for permission. In the live guide, the person reviews the recognized permission before it reaches the robot.")
        flow("CONFIRM")
    else:
        st.info("The input supplies no usable new task. Hold the current state and ask the person to repeat or clarify.")
        flow("IDLE")
    st.write("Try Ambiguous request, then Wrong color heard. In the first case the words are transcribed correctly but the target is missing. In the second case the parser has a target, but the person must correct it. That is why clarification and confirmation solve different problems.")
    return True


def readiness_activity():
    st.write("Fetching the right cup does not tell the robot that the person is ready to receive it. This activity shows why arriving, offering, and transferring must be separate decisions.")
    st.markdown("**Read the display**")
    st.write("The robot marker shows where the robot is. The highlighted box shows its interaction phase. EXECUTING means travelling or loading. WAIT_READY means the robot has returned, is offering the cup, and is waiting for the person. COMPLETE means transfer has been authorized.")
    demo = st.session_state.setdefault("tutorial-handover", new_trial(MODES[2]))
    st.markdown("**Part A. Try readiness before the offer**")
    st.write("Select Start blue. Before advancing the robot, select Send early Ready. Look at the phase and transferred-cup value. The robot should continue retrieving the cup and should not remember this early signal as permission for a later transfer.")
    cols = st.columns(2)
    if cols[0].button("Start blue", disabled=demo["state"]["phase"] != "IDLE"):
        dispatch(demo, event("START", "blue"), source="demo")
    if cols[1].button("Send early Ready", disabled=demo["state"]["phase"] != "EXECUTING"):
        dispatch(demo, event("READY"), source="demo")
    st.markdown("**Part B. Follow the trip to the offer**")
    st.write("Select Next robot step repeatedly. Watch it travel to blue, load the cup onto its simulated tray, return to the person, and enter WAIT_READY. Each click reveals one step of the teaching diagram.")
    if st.button("Next robot step", disabled=demo["state"]["phase"] != "EXECUTING"):
        dispatch(demo, event("TICK"))
    st.markdown("**Part C. Compare three outcomes**")
    st.write("At WAIT_READY, choose Ready now to transfer, Let offer expire to see timeout recovery, or Cancel handover to stop while retaining the cup. Reset and repeat with a different outcome. Compare the feedback and the final row in the event trace.")
    cols = st.columns(3)
    offered = demo["state"]["phase"] == "WAIT_READY"
    if cols[0].button("Ready now", disabled=not offered):
        dispatch(demo, event("READY"), source="demo")
    if cols[1].button("Let offer expire", disabled=not offered):
        dispatch(demo, event("TIMEOUT"), source="demo")
    if cols[2].button("Cancel handover", disabled=demo["state"]["phase"] not in ("EXECUTING", "WAIT_READY")):
        dispatch(demo, event("STOP"), source="demo")
    if st.button("Reset readiness activity"):
        demo = st.session_state["tutorial-handover"] = new_trial(MODES[2])
    show_trial(demo)
    st.info("The rule you will implement next must check two things together. The robot is offering the cup, and a new READY event has arrived. Neither condition alone authorizes transfer.")
    return True


def code_activity(work):
    st.write("You will now repair the rule that protects the last step of the handover. The starter returns release whenever the robot is in WAIT_READY, so even an unrelated timer event can release the cup. Your change makes release depend on the person's readiness.")
    st.markdown("**1. Run the starter and find the error**")
    st.write("Before editing, select Replay readiness checks. Open Early and missing readiness. Find the first unexpected transition. The expected phase is WAIT_READY with the cup still held. The starter may instead show COMPLETE. Use the event column to identify what triggered that release.")
    st.markdown("**2. Edit the code here**")
    st.write("phase is the robot's current interaction phase. kind is the incoming event. The condition must require both WAIT_READY and READY. Replace the broad release condition, leave the other TODOs for Mission 1, and select Save controller.")
    flow("WAIT_READY")
    st.code('if phase == "WAIT_READY" and kind == "READY":\n    return "release"', language="python")
    path = controller_editor(work, "tutorial3")
    source = path.read_text(encoding="utf-8-sig")
    st.markdown("**3. Replay and compare**")
    st.write("Select Replay readiness checks again after saving. Normal transfer and Early and missing readiness should pass. Cancel while offering can still fail because you will implement cancellation in Mission 1.")
    if st.button("Replay readiness checks", key="tutorial-replay"):
        try:
            results = {row["case"]: row for row in scripted_checks(load_controller(source))}
            work["tutorial_checks"] = {"source": source, "rows": [results[name] for name in
                ("Normal transfer", "Early and missing readiness", "Cancel while offering")]}
        except Exception as error:
            st.error(f"The checks could not run. Inspect your Python code. {error}")
    saved = work.get("tutorial_checks", {})
    for result in saved.get("rows", []):
        with st.expander(f"{'Pass' if result['passed'] else 'Needs work'} · {result['case']}", expanded=not result["passed"]):
            if result["first_mismatch"]:
                st.write("This is the first place the controller did something different from the expected behavior.")
                st.json(result["first_mismatch"])
            last = result["trace"][-1]["after"]
            stations(last)
            flow(last["phase"])
            st.dataframe([{"Event": row["event"], "Decision": row["decision"], "Before": row["before"]["phase"],
                           "After": row["after"]["phase"], "Transferred": row["after"]["delivered"]}
                          for row in result["trace"]], hide_index=True)
    ready = saved.get("source") == source and bool(saved.get("rows")) and all(row["passed"] for row in saved["rows"][:2])
    if not ready:
        st.caption("Save the corrected readiness rule and pass the first two checks to continue.")
    return ready


def modes_activity():
    st.write("The same delivery task can divide control between person and robot in different ways. Here you will redirect a blue-cup task to red and see which part of that change the person must handle.")
    st.table([
        {"Mode": MODES[0], "Person does": "Steers the robot and chooses when to load and offer", "Robot does": "Applies bounded velocity commands"},
        {"Mode": MODES[1], "Person does": "Speaks a goal, corrects it, and confirms it", "Robot does": "Drives the confirmed route and offers the cup"},
        {"Mode": MODES[2], "Person does": "Starts the supplied policy and intervenes if the goal changes", "Robot does": "Executes the selected delivery"},
    ])
    st.markdown("**1. Choose a mode and inspect the checkpoint**")
    st.write("The marker starts at the yellow correction point, 2 m from the person. Blue was selected, but the person now wants red. This is the same interruption point used in the later Gazebo trials.")
    mode = st.radio("Control mode to explore", MODES)
    key = f"tutorial-mode-{MODES.index(mode)}"
    reset = st.button("Reset this mode")
    if key not in st.session_state or reset:
        demo = st.session_state[key] = new_trial(mode, "changed")
        demo["state"].update(phase="EXECUTING", position=2, target="blue", confirmed=True,
                             checkpoint_seen=True, waiting_for_change=True)
    demo = st.session_state[key]
    st.markdown("**2. Redirect the task using this mode's controls**")
    if mode == MODES[0]:
        st.write("Select Red is now the goal, then Move diagram marker toward red. Here you supply the movement. In Gazebo you will steer the robot with W/S/A/D.")
        if st.button("Red is now the goal"):
            dispatch(demo, event("SET_GOAL", "red"), source="demo")
        if st.button("Move diagram marker toward red", disabled=demo["state"]["waiting_for_change"]):
            dispatch(demo, event("RIGHT"), source="demo")
    elif mode == MODES[1]:
        st.write("Send a correction, inspect the new red goal, then confirm it. The robot must wait for the new confirmation. Next robot step is available afterward.")
        if st.button("Send correction to red", disabled=demo["state"]["target"] != "blue"):
            dispatch(demo, event("CORRECT", "red"), lambda *_: "select", source="demo")
        if st.button("Confirm red goal", disabled=demo["state"]["phase"] != "CONFIRM"):
            dispatch(demo, event("CONFIRM"), lambda *_: "begin", source="demo")
        if st.button("Next robot step", disabled=demo["state"]["phase"] != "EXECUTING" or demo["state"]["waiting_for_change"]):
            dispatch(demo, event("TICK"), lambda *_: "advance")
    else:
        st.write("First stop the blue task. Then select Run red task. The supplied policy chooses the movement after you start it. The diagram remains paused until you give that explicit new start.")
        if st.button("Stop blue task", disabled=demo["state"]["phase"] != "EXECUTING"):
            dispatch(demo, event("STOP"), source="demo")
        if st.button("Run red task", disabled=demo["state"]["phase"] != "CANCELLED"):
            dispatch(demo, event("START", "red"), source="demo")
        if st.button("Next robot step", key="autonomous-demo-step", disabled=demo["state"]["phase"] != "EXECUTING" or demo["state"]["waiting_for_change"]):
            dispatch(demo, event("TICK"))
    st.markdown("**3. Read the result and try another mode**")
    show_trial(demo)
    st.write("Compare which action changed the selected cup, whether a new confirmation was needed, and who chose the movement. In all modes, the person will still authorize the final transfer with Ready.")
    return True
