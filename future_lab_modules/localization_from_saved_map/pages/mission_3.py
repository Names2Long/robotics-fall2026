from pathlib import Path

from analysis.localization import localization_decision
from lab.autosave import submission_root
from lab.completion import current_signature
from lab.controls import prediction
from lab.evidence import artifact, evidence_id, load_json
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_3 import CONDITIONS, evaluate

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "good_initial_pose": "Good initial pose", "incorrect_initial_pose": "Incorrect initial pose",
    "ambiguous_location": "Ambiguous location", "degraded_sensor": "Degraded scan",
}
GUIDANCE = {
    "good_initial_pose": "Set a pose near the simulated robot with a matching heading.",
    "incorrect_initial_pose": "Set a pose at least 1 m away or rotate it at least 90°. Move through distinctive geometry.",
    "ambiguous_location": "Initialize in a visually similar corridor or symmetric area. Look for competing particle clusters.",
    "degraded_sensor": "Restart in degraded mode. The proxy retains about half of scans and adds range noise.",
}


def _trial(st, condition, selected_map_id, map_path):
    with st.expander(LABELS[condition], expanded=condition == "good_initial_pose"):
        st.write(GUIDANCE[condition])
        forecast = prediction(
            st, "mission_3." + condition,
            {"condition": condition, "selected_map": selected_map_id},
            "Before this trial, predict the initial particle distribution, change over time, and whether the estimate will reach the correct place.",
            min_chars=30,
        )
        if forecast is None:
            return None, None, None
        mode = "degraded" if condition == "degraded_sensor" else "normal"
        st.write("Stop the prior localization launch with Ctrl+C before starting this condition. The command starts a fresh TurtleBot3 House, loads your chosen House map, and starts AMCL. Keep the robot still while setting its initial pose. In RViz, use 2D Pose Estimate to click a map location and drag the arrow to set heading. Then drive slowly with the teleop terminal.")
        st.code(
            "cd /workspace/week06_slam_localization\n"
            f"bash scripts/launch_localization.sh '{map_path}' {mode}",
            language="bash",
        )
        st.caption("This is the saved map selected at the start of Mission 3. Use the same map in all four trials.")
        st.write("Open another terminal for teleoperation. Click inside it and press `w` more than once to build forward speed. Use `a` or `d` to turn and `s` or Space to stop. In RViz, add Map and LaserScan by topic. If a particle cloud topic is available, add its PoseArray display to see competing pose hypotheses.")
        st.code("cd /workspace/week06_slam_localization\nsource /opt/ros/jazzy/setup.bash\nexport ROS_DOMAIN_ID=26\nros2 run turtlebot3_teleop teleop_keyboard", language="bash")
        st.write("While AMCL is running, start the recorder in a separate terminal. It collects pose and uncertainty samples for 30 seconds and saves the JSON file shown below. Keep driving gently during that interval.")
        st.code(
            "cd /workspace/week06_slam_localization\n"
            "source /opt/ros/jazzy/setup.bash\n"
            "source ros2_ws/install/setup.bash\n"
            "export ROS_DOMAIN_ID=26\n"
            "ros2 run course_slam_tools localization_recorder --ros-args \\\n"
            f"  -p condition:={condition} -p duration:=30.0 \\\n"
            f"  -p output:=runtime/evidence/{condition}.json",
            language="bash",
        )
        st.caption("Expected: a JSON file with pose samples and summary metrics. If it contains no samples, check `/amcl_pose`, `/scan`, map frame alignment, and the initial pose setting.")
        st.write("For a visual record, make RViz visible, run this command, then switch back to RViz during the four-second delay.")
        st.code(
            "cd /workspace/week06_slam_localization\n"
            f"python3 scripts/capture_desktop.py --output runtime/evidence/{condition}.png --delay 4",
            language="bash",
        )
        local = ROOT / "runtime" / "evidence"
        item = artifact(None, local / f"{condition}.json") or artifact(None, submission_root() / "mission_3" / f"trial_{condition}.json")
        evidence = load_json(item)
        if evidence and evidence.get("condition") != condition:
            st.error(f"This file says {evidence.get('condition')!r}. Expected {condition!r}.")
            evidence = None
        if evidence and not isinstance(evidence.get("metrics"), dict):
            st.error("This trial has no metrics object. Rerun the localization recorder.")
            evidence = None
        saved_screens = sorted((submission_root() / "mission_3").glob(f"rviz_{condition}.*"))
        screen = (artifact(None, local / f"{condition}.png")
                  or (artifact(None, saved_screens[0]) if saved_screens else None))
        if screen is None:
            st.caption(f"Save an RViz screenshot to `runtime/evidence/{condition}.png`.")
        if evidence:
            metrics = evidence["metrics"]
            st.dataframe([metrics], hide_index=True, width="stretch")
            rows = evidence.get("samples", [])
            if rows:
                import pandas as pd
                frame = pd.DataFrame(rows)
                if {"time", "covariance_trace"}.issubset(frame.columns):
                    st.line_chart(frame.set_index("time")[["covariance_trace"]], height=240)
                    st.caption("Covariance trace is modeled uncertainty, not physical position error.")
                if {"reference_x", "reference_y", "x", "y", "time"}.issubset(frame.columns):
                    frame["position_error_m"] = ((frame["x"] - frame["reference_x"]) ** 2 + (frame["y"] - frame["reference_y"]) ** 2) ** .5
                    st.line_chart(frame.set_index("time")[["position_error_m"]], height=240)
            if not metrics.get("reference_available"):
                st.info("No certified map-frame reference was recorded. Judge correctness from RViz and Gazebo observations. Do not call covariance a measured position error.")
            st.write("Prediction:", forecast)
        text_response(
            st, f"mission_3.{condition}.observation",
            "Record the initial hypothesis, particle cloud or competing clusters, behavior over time, and evidence for or against correct localization. Compare with your saved prediction.",
        )
        widget = f"field.mission_3.{condition}.correctness"
        if widget not in st.session_state:
            st.session_state[widget] = response(st, f"mission_3.{condition}.correctness", "Choose…")
        choice = st.selectbox(
            "Did the estimate converge to the correct place?",
            ("Choose…", "Correct", "Incorrect", "Uncertain"),
            key=widget,
        )
        set_response(st, f"mission_3.{condition}.correctness", choice)
        return evidence, item, screen


def render(st):
    st.header("Mission 3: Localize in the saved map")
    st.write("Use one selected map for all four conditions. Restart between trials so an earlier pose belief cannot carry over. The four panels preserve a prediction before showing each result.")
    st.subheader("1. Choose the reference map")
    widget = "field.mission_3.selected_map"
    if widget not in st.session_state:
        st.session_state[widget] = response(st, "mission_3.selected_map", "Choose…")
    selection = st.selectbox("Saved map for all four AMCL trials", ("Choose…", "Mission 1", "Mission 2"), key=widget)
    set_response(st, "mission_3.selected_map", selection)
    selected_map = text_response(st, "mission_3.map_choice", "Why choose this map? Cite visible structure and at least two measured properties from Missions 1 and 2.")
    if selection == "Choose…" or len(selected_map.strip()) < 40:
        st.info("Choose and justify one saved map before starting the trials.")
        return
    st.button("Check saved trial files", key="m3.refresh")
    mission = "mission_1" if selection == "Mission 1" else "mission_2"
    run = "mission1" if mission == "mission_1" else "mission2"
    runtime_path = ROOT / "runtime" / "maps" / run / "map.yaml"
    map_path = runtime_path if runtime_path.is_file() else submission_root() / mission / "map.yaml"
    selected_map_id = evidence_id(selection, st.session_state["evidence"].get(mission), selected_map)
    trials = {}
    items = {}
    screens = {}
    for condition in CONDITIONS:
        evidence, item, screen = _trial(st, condition, selected_map_id, map_path)
        if evidence:
            trials[condition] = evidence
            items[condition] = item
        if screen:
            screens[condition] = screen

    if trials:
        st.subheader("Compare conditions")
        rows = []
        for condition in CONDITIONS:
            metrics = trials.get(condition, {}).get("metrics", {})
            rows.append({
                "Condition": LABELS[condition], "Samples": metrics.get("sample_count"),
                "Covariance concentration time (s)": metrics.get("convergence_time"),
                "Final covariance trace": metrics.get("final_covariance"),
                "Final position error (m), if reference exists": metrics.get("final_position_error"),
                "Correct place?": response(st, f"mission_3.{condition}.correctness", "Not assessed"),
            })
        st.dataframe(rows, hide_index=True, width="stretch")
        st.caption("Concentration time uses covariance only. Correct convergence needs independent reference evidence. An absent reference is reported as unavailable, not zero error.")

    st.subheader("Degraded evidence and recovery")
    text_response(st, "mission_3.knowing_where", "What evidence would justify saying the robot knows where it is? Distinguish pose estimate, particle spread, scan agreement, and independent correctness evidence.")
    text_response(st, "mission_3.recovery", "Compare good and incorrect initial poses. What changed in covariance, pose, and RViz, and what helped or hindered recovery?")
    text_response(st, "mission_3.sensor_effect", "Compare normal and degraded sensing. Did uncertainty, convergence speed, competing hypotheses, or recovery change? Relate this to Lab 5 without treating covariance as guaranteed true error.")
    text_response(st, "mission_3.deployment_limit", "Describe a dangerous false-confidence case, who could be affected, and a detection or safe fallback.")

    st.subheader("A small localization-safety rule")
    st.write("The following rule sees only recorded localization evidence, not simulation truth. Change its thresholds, apply it to all four trials, and identify where it could still be confidently wrong.")
    covariance_limit = st.slider("Maximum acceptable final covariance trace", .1, 2.0, .5, .05, key="m3.policy.covariance")
    convergence_limit = st.slider("Maximum acceptable concentration time (s)", 1., 30., 10., 1., key="m3.policy.convergence")
    set_response(st, "mission_3.policy", {"covariance_limit": covariance_limit, "convergence_limit": convergence_limit})
    policy_rows = []
    for condition in CONDITIONS:
        metrics = trials.get(condition, {}).get("metrics", {})
        policy_rows.append({"Condition": LABELS[condition], "Rule output": localization_decision(metrics, covariance_limit, convergence_limit),
                            "Your independent correctness judgment": response(st, f"mission_3.{condition}.correctness", "Not assessed")})
    st.dataframe(policy_rows, hide_index=True, width="stretch")
    text_response(st, "mission_3.policy_reasoning", "Use all four condition results to explain when this rule would slow, stop, or ask for help. Identify a false-confidence risk, a stronger check, and a person affected by a wrong decision.")

    check = evaluate(trials, st.session_state["responses"])
    render_check(st, check)
    if len(screens) < 2:
        st.info("Include RViz screenshots for at least two different conditions.")
    if st.button("Check and save Mission 3", type="primary", disabled=not check.passed or len(screens) < 2):
        previous = st.session_state["evidence"].get("mission_3")
        st.session_state["evidence"]["mission_3"] = trials
        signature = current_signature(st, "mission_3")
        uploads = {f"trial_{condition}.json": item for condition, item in items.items()}
        uploads.update({f"rviz_{condition}{Path(item.name).suffix.lower()}": item for condition, item in screens.items()})
        try:
            save_mission(
                "mission_3", {"trials": trials, "policy": st.session_state["responses"]["mission_3.policy"],
                              "state_signature": signature},
                st.session_state["responses"], uploads, state_signature=signature,
            )
        except (OSError, ValueError) as failure:
            if previous is None: st.session_state["evidence"].pop("mission_3", None)
            else: st.session_state["evidence"]["mission_3"] = previous
            st.error(f"Mission files were not saved: {failure}")
        else:
            complete_mission(st, "mission_3", signature)
            st.success("Four trials, screenshots, explanations, and decision rule saved.")
