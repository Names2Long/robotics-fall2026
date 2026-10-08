from pathlib import Path

from lab.autosave import submission_root
from lab.completion import current_signature
from lab.controls import prediction
from lab.evidence import artifact, evidence_id, load_json, runtime_map, validate_map_bundle
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check, show_map, text_response
from missions.mission_2 import evaluate
from lab_config import WORLD_ID

ROOT = Path(__file__).resolve().parents[1]


def comparison_rows(first, second):
    """Describe only measurements available in both saved map analyses."""
    def values(run):
        metrics = run.get("metrics", {})
        known = metrics.get("known_fraction")
        area = metrics.get("map_area_m2")
        minutes = run.get("duration_minutes")
        known_area = known * area if isinstance(known, (int, float)) and isinstance(area, (int, float)) else None
        return {
            "Elapsed time (min)": minutes,
            "Known fraction (%)": 100 * known if isinstance(known, (int, float)) else None,
            "Known area (m²)": known_area,
            "Speckle fraction (%)": 100 * metrics["speckle_fraction"] if isinstance(metrics.get("speckle_fraction"), (int, float)) else None,
            "Quality score (0 to 100)": run.get("quality_score"),
            "Known area per minute (m²/min)": known_area / minutes if known_area is not None and isinstance(minutes, (int, float)) and minutes > 0 else None,
        }

    left, right = values(first), values(second)
    rows = []
    for label in left:
        a, b = left[label], right[label]
        rows.append({
            "Measure": label,
            "Mission 1": round(a, 2) if isinstance(a, (int, float)) else "unavailable",
            "Mission 2": round(b, 2) if isinstance(b, (int, float)) else "unavailable",
            "Mission 2 minus Mission 1": round(b - a, 2) if isinstance(a, (int, float)) and isinstance(b, (int, float)) else "unavailable",
        })
    return rows


def render(st):
    st.header("Mission 2: Compare mapping strategies")
    first = st.session_state["evidence"].get("mission_1")
    st.write("Mission 1 was your first route and first map. In this mission you will start the same world again with the robot at its original start position and an empty SLAM map. Drive one different route through that world. You will compare the new map and its completion time with the Mission 1 results. You are not being asked to drive two more routes.")
    st.subheader("1. Plan your second route")
    forecast = prediction(
        st, "mission_2.strategy", {"first_evidence_id": evidence_id(first), "world": WORLD_ID},
        "Describe how your new route will differ from the Mission 1 route. Predict whether it will map the accessible space faster or produce a clearer map, and explain why.",
        min_chars=40,
    )
    if forecast is None:
        return

    st.subheader("2. Reset the simulation and make map two")
    st.write("First stop the robot with `s` or Space. Stop the Mission 1 teleop process with Ctrl+C. In the original mapping terminal, press Ctrl+C and wait for SLAM Toolbox to exit. Keep RViz open. Then run the reset command below in a new terminal. It closes any Gazebo processes left behind by the first launch and leaves the saved Mission 1 files untouched.")
    st.code("cd /workspace/week06_slam_localization\nbash scripts/reset_mapping.sh", language="bash")
    st.write("After the reset reports that the old world stopped, run the next command. It starts a new Gazebo world, respawns the robot at the same start position, and starts SLAM Toolbox with an empty map. The launcher refuses to start if the old mapping system is still active.")
    st.code(
        "cd /workspace/week06_slam_localization\n"
        "bash scripts/launch_mapping.sh",
        language="bash",
    )
    st.write("Confirm in Gazebo that the robot is back at its original start. Wait for RViz to receive the new `/map`. It should replace the old view with a small new map around the robot. If RViz keeps showing the old map, close it and reopen it with the Guided Tutorial 3 RViz command. Use teleop again to drive only your second route. Start timing with the first movement. Visit the accessible space until the main rooms and corridors have recognizable outlines, then stop the robot and record the elapsed minutes. A faster run only helps if the resulting map is useful.")
    st.subheader("3. Save and measure map two")
    st.write("Before running the next command, replace `room_by_room` with a short label for your second route and replace `7` after `--duration-min` with the minutes you just measured. This saves Mission 2 files in a separate folder, so it does not replace your Mission 1 map. Keep SLAM running while the map saver runs.")
    st.code(
        "cd /workspace/week06_slam_localization\n"
        "source /opt/ros/jazzy/setup.bash\n"
        "export ROS_DOMAIN_ID=26\n"
        "mkdir -p runtime/maps/mission2\n"
        "ros2 run nav2_map_server map_saver_cli -f runtime/maps/mission2/map\n"
        "python3 scripts/analyze_map.py --yaml runtime/maps/mission2/map.yaml "
        "--strategy room_by_room --duration-min 7 "
        "--output runtime/maps/mission2/evidence.json",
        language="bash",
    )
    st.caption("The analyzer records the route label, your elapsed time, and measurements computed from the saved PGM map. It does not time the run for you.")
    st.write("Arrange RViz so the map, scan, and robot pose are visible. Run the command below, then switch to RViz during the four-second delay. Check that the saved image shows the intended evidence.")
    st.code("cd /workspace/week06_slam_localization\npython3 scripts/capture_desktop.py --output runtime/maps/mission2/rviz.png --delay 4", language="bash")
    local_evidence, local_yaml, local_image = runtime_map("mission2")
    evidence_item, yaml_item, image_item = local_evidence, local_yaml, local_image
    st.button("Check saved comparison files", key="m2.refresh")
    saved_screens = sorted((submission_root() / "mission_2").glob("rviz_screenshot.*"))
    screenshot = (artifact(None, ROOT / "runtime/maps/mission2/rviz.png")
                  or (artifact(None, saved_screens[0]) if saved_screens else None))
    second = load_json(evidence_item)
    metrics, error = validate_map_bundle(second, yaml_item, image_item)
    if error: st.info(error)
    if first and second and metrics is not None:
        st.subheader("4. Compare both maps")
        a, b = st.columns(2)
        with a:
            first_pgm = artifact(None, submission_root() / "mission_1" / "map.pgm")
            show_map(st, first_pgm, "First strategy", width=450)
        with b: show_map(st, image_item, "Second strategy", width=450)
        st.write("The table below reads each run's `evidence.json`, which the analyzer created from its saved map. Known fraction is the percentage of cells labeled free or occupied. Known area multiplies that fraction by the map's area. Speckle fraction measures tiny isolated occupied patches. The score combines coverage and map-shape heuristics. Elapsed time is the value you entered, not a measured ROS timestamp.")
        st.dataframe(comparison_rows(first, second), hide_index=True, width="stretch")
        st.caption("Known area per minute is a rough efficiency indicator. Map bounds may differ, and neither a larger known area nor a higher score proves geometric correctness. Compare the visible walls and unknown rooms too.")

    st.subheader("5. Explain the comparison")
    text_response(st, "mission_2.comparison", "Using the table above, cite both elapsed times and at least two map measurements. Which route gave more useful coverage for the time spent? Was your prediction supported? Explain any tradeoff between speed and map quality.")
    text_response(st, "mission_2.map_choice", "Look at both map images. Which would you trust more for a later robot task? Point to visible evidence such as wall alignment, missing rooms, or duplicate structures. State one limit of what these images and numbers can prove.")
    check = evaluate(first, second if metrics is not None else None, st.session_state["responses"])
    render_check(st, check)
    if st.button("Check and save Mission 2", type="primary", disabled=not check.passed or screenshot is None):
        prior = st.session_state["evidence"].get("mission_2")
        st.session_state["evidence"]["mission_2"] = second
        signature = current_signature(st, "mission_2")
        try:
            save_mission(
                "mission_2", {"strategy_1": first, "strategy_2": second, "state_signature": signature},
                st.session_state["responses"],
                {"analysis.json": evidence_item, "map.yaml": yaml_item, "map.pgm": image_item,
                 "rviz_screenshot" + Path(screenshot.name).suffix.lower(): screenshot},
                state_signature=signature,
            )
        except (OSError, ValueError) as failure:
            if prior is None: st.session_state["evidence"].pop("mission_2", None)
            else: st.session_state["evidence"]["mission_2"] = prior
            st.error(f"Mission files were not saved: {failure}")
        else:
            complete_mission(st, "mission_2", signature)
            st.success("Both strategy records are saved for comparison.")
