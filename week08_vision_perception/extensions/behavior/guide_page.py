"""Archived behavior activity. Not imported by the required Lab 7 guide."""
from dataclasses import asdict
import pandas as pd
from evaluation.behavior import BehaviorConfig, evaluate_sequences, DEFAULT_RULE, transition
from perception.experiments import signature
from lab.ui import text_response, mission_status
from lab.submissions import store_run


def render(st):
    st.header("Mission 3: use visual evidence to control behavior")
    from pages.guidance import mission3
    mission3(st)
    rule = text_response(st,"implementation.policy","Your state-transition expression",90).strip()
    rule_ok = False
    try:
        BehaviorConfig(transition_rule=rule)
        rule_ok = True
        st.success("Transition expression returns a valid state for every Boolean combination")
    except ValueError as error: st.info(str(error))
    st.write("Define when a simulated robot searches, approaches or stops. Test your policy against changing observations, including a confidently wrong target. Correct detection and correct action are different outcomes.")
    st.subheader("Guided steering and timing")
    st.latex(r"e_x = x_{\mathrm{target}} - W/2,\qquad e_{\mathrm{normalized}} = 2x_{\mathrm{target}}/W - 1")
    st.markdown("x increases to the right in the image. A target to the right has positive error. In this ROS convention positive angular velocity turns left, so the steering command has the opposite sign. The policy rotates in place until centered, then moves forward. This is image-space correction, not a measurement of the target's world coordinates.")
    st.table([{"State": "SEARCH", "Motion": "Rotate slowly, no forward movement", "When": "You permit search after a fresh low-confidence or missing-target report"},
              {"State": "APPROACH", "Motion": "Steer in place or move forward when centered", "When": "Enough consistent, fresh detections have arrived"},
              {"State": "STOP", "Motion": "Zero velocity", "When": "Stale or absent messages, unconfirmed evidence, or the image-area goal"}])
    st.markdown("Freshness means time since image capture, not only time since a message arrived. A transport timeout also stops motion if updates cease. Requiring several consistent frames helps reject brief false alarms, but delays action. A persistent false detection can still fool this policy.")
    st.warning("The image-area goal is an illustrative simulation condition. It is not a calibrated physical stopping distance. Searching also involves motion and would need a separate safety assessment around real people.")
    st.markdown("**1. Define your transition conditions.** Values are bounded to the lab's simulated speed limits.")
    saved = st.session_state["settings"].get("policy", asdict(BehaviorConfig()))
    a, b, c = st.columns(3)
    config = BehaviorConfig(
        min_confidence=a.slider("Minimum confidence", .05, 1., float(saved["min_confidence"]), .05),
        stale_after=b.slider("Maximum capture age (seconds)", .05, 2., float(saved["stale_after"]), .05),
        confirmation_frames=c.slider("Consecutive consistent frames", 1, 10, int(saved["confirmation_frames"])),
        stop_area=a.slider("Image-area goal fraction", .05, .4, float(saved["stop_area"]), .01),
        center_deadband=b.slider("Center tolerance (normalized)", .01, .5, float(saved["center_deadband"]), .01),
        max_center_jump=c.slider("Maximum center change per frame", .05, 1., float(saved["max_center_jump"]), .05),
        loss_action=st.selectbox("Fresh report with no reliable target", ["STOP", "SEARCH"], index=["STOP", "SEARCH"].index(saved["loss_action"])),
        transition_rule=rule if rule_ok else DEFAULT_RULE,
    )
    st.session_state["settings"]["policy"] = asdict(config)
    st.markdown("**2. Run the sequence trials.** Each trial lasts 2.4 simulated seconds at 10 Hz. The visible trial uses your chosen detector's saved observation. Other trials normalize the target geometry and inject failures or motion to isolate policy behavior. This is not a physical goal-reaching experiment.")
    learned = st.session_state["evidence"].get("mission_2")
    usable = learned and learned.get("schema_version") == 2
    if not usable: st.info("Run Mission 2 first to connect these trials to your recorded visual evidence.")
    if st.button("Run and save all policy trials", type="primary", disabled=not usable or not rule_ok):
        method = learned.get("preferred_method","learned")
        source = st.session_state["evidence"].get("mission_1") if method == "classical" else learned
        row = next(r for r in source["rows"] if r["image_id"] == "normal_1")
        box = row.get("bbox") or [240,160,0,0]
        x,y,w,h = box
        seed = {"detected": row["detected"] and (method == "classical" or row["confidence"] >= learned["selected_threshold"]), "confidence": row["confidence"], "center_offset": max(-1.,min(1.,2*(x+w/2)/480-1)), "area_fraction": min(1.,w*h/(480*320))}
        result = evaluate_sequences(config, seed)
        store_run(st, "mission_3", {"config": asdict(config), "seed": seed, "result": result, "perception_run": signature(learned),"source_run":signature(source),"source_method":method})
    evidence = st.session_state["evidence"].get("mission_3")
    if evidence and "timeline" in evidence.get("result", {}):
        result = evidence["result"]
        st.dataframe(result["summaries"], hide_index=True)
        if st.session_state["history"]:
            with st.expander("Compare with your previous policy run"):
                previous = st.session_state["history"][-1]
                st.write("Previous settings", previous["config"])
                st.dataframe(previous["summaries"], hide_index=True)
        st.caption("A step is 0.1 s. Stopped opportunity steps include deliberate confirmation waits. Incorrect approaches use simulator truth unavailable to the policy. A blank delay means forward motion never began.")
        chosen = st.selectbox("Inspect a sequence", [r["scenario"] for r in result["summaries"]])
        rows = pd.DataFrame([r for r in result["timeline"] if r["scenario"] == chosen])
        st.caption("Confidence (unitless)")
        st.line_chart(rows.set_index("time")[["confidence"]],height=170)
        st.caption("Horizontal target offset (normalized)")
        st.line_chart(rows.set_index("time")[["center_offset"]],height=170)
        left,right = st.columns(2)
        left.caption("Forward command (m/s)")
        left.line_chart(rows.set_index("time")[["linear_x"]],height=170)
        right.caption("Turning command (rad/s)")
        right.line_chart(rows.set_index("time")[["angular_z"]],height=170)
        st.dataframe(rows, hide_index=True)
        st.info("The persistent false-target sequence may produce incorrect approaches even when timing constraints pass. Explain that limitation. Passing the timing checks is not a safety certificate.")
    with st.expander("Trace the same policy through live ROS topics"):
        st.markdown("The guide already ran the sequence experiment. This exercise exposes the same policy through ROS and a synthetic observation publisher. It does not launch a physical robot or infer distance from a real camera. Keep all commands in the virtual desktop.")
        st.markdown("**Terminal 1:** source the lab environment, then start the policy demo. It loads your saved policy settings when available, publishes timestamped test observations and routes commands through the guard on isolated `/lab7/...` topics. Leave it running.")
        st.code("cd /workspace/week08_vision_perception\nsource scripts/ros_env.sh\nbash scripts/launch_policy_demo.sh", language="bash")
        st.markdown("**Terminal 2:** inspect the graph and messages. Ctrl+C stops an echo command before starting the next. Stop Terminal 1 when finished.")
        st.code("cd /workspace/week08_vision_perception\nsource scripts/ros_env.sh\nros2 node list\nros2 topic echo /lab7/perception/target\n# After Ctrl+C\nros2 topic echo /lab7/cmd_vel", language="bash")
    text_response(st, "mission_3.trace", "Trace an image or injected observation through detection and the policy command. Use a timeline to explain capture age, confirmation and steering. If you ran ROS, distinguish the guarded output from the guide's policy command.")
    text_response(st, "mission_3.failure", "Compare two policy configurations or sequences. Use incorrect approaches, stopped opportunity steps or action delay. Which failure comes from perception, timing or policy, and what additional safeguard would you need?")
    mission_status(st, "mission_3")
