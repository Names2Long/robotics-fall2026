from pathlib import Path

from lab.autosave import submission_root
from lab.completion import current_signature
from lab.controls import prediction
from lab.evidence import artifact, load_json, runtime_map, validate_map_bundle
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check, show_map, text_response
from missions.mission_1 import evaluate
from lab_config import WORLD_ID

ROOT = Path(__file__).resolve().parents[1]


def render(st):
    st.header("Mission 1: Build and inspect a map")
    st.write("In this mission you will use keyboard teleoperation to drive the TurtleBot3 around the simulated world. As you move, watch RViz build the occupancy-grid map from LiDAR scans and motion estimates. Visit the accessible corridors, walls, and obstacle sides until the main space is represented. Then save the map and explain what your route revealed.")
    st.image(str(ROOT / "assets" / "turtlebot3_house_plan.png"), caption="TurtleBot3 House wall plan. Use the room openings to plan a route, then check Gazebo for furniture and the exact traversable space.", width=760)
    st.write("The robot starts near the center-left of the house at about x = -2 m, y = -0.5 m. Internal walls form rooms, openings, and places that a single LiDAR scan cannot see. Plan a route through accessible areas and return to one distinctive wall or junction. Do not assume every room is reachable from your chosen path. Compare the plan with the live Gazebo view before driving.")

    st.subheader("1. Plan before driving")
    forecast = prediction(
        st, "mission_1.route", {"world": WORLD_ID, "run": 1},
        "Describe your route, a place you will revisit, and where you predict map coverage or alignment may be weak.",
        min_chars=40,
    )
    if forecast is None:
        st.info("Save the plan before running the robot. Your original prediction is kept separately from later analysis.")
        return

    st.subheader("2. Continue the mapping session and drive")
    st.write("Keep the Gazebo, SLAM Toolbox, and RViz windows from Guided Tutorial 3 open. Do not launch them again. Open a new terminal for teleop. Start timing when the robot first moves. Drive your planned route while watching the map appear in RViz. Continue until the accessible rooms and corridors have recognizable wall outlines and no large unexplored pockets remain along your route. Space outside walls can remain unknown. Aim for the shortest time that still produces a useful map, but slow down near obstacles and turns so the robot stays safe and the scans remain useful. Stop timing when you decide the map is complete enough to save, and write down the elapsed minutes.")
    with st.expander("New terminal: drive with the keyboard", expanded=True):
        st.code("cd /workspace/week06_slam_localization\nsource /opt/ros/jazzy/setup.bash\nexport ROS_DOMAIN_ID=26\nros2 run turtlebot3_teleop teleop_keyboard", language="bash")
        st.write("Click inside the teleop terminal so it receives your key presses. Press `w` repeatedly to increase forward velocity one step at a time. A single press may produce very slow movement. Press `x` repeatedly to reduce forward velocity. Press `a` or `d` repeatedly to adjust angular velocity. Press `s` or Space to force a stop. The terminal prints the current target speeds. Use small changes and avoid driving into obstacles.")
        st.caption("The keys control the teleop terminal, not the Streamlit page or the Gazebo window. Return focus to this terminal before pressing them.")
    st.write("In the RViz window you opened during Guided Tutorial 3, compare the live scan with existing map edges. On a revisit, look for a change to already mapped structure, not only new cells. Select each display in the left panel to check its Status and Topic.")
    st.warning("Avoid rapid rotation and do not edit the saved PGM or evidence JSON by hand.")

    st.subheader("3. Save and analyze")
    st.write("Stop the robot with `s` or Space. Leave SLAM running while you save the map in another terminal. Before running the command below, replace `perimeter_then_interior` with a short label for the route you actually drove and replace `7` after `--duration-min` with the elapsed minutes you recorded. The analyzer uses your duration as a label. It cannot measure driving time automatically. Start the command from the Lab 6 directory, not `/workspace`.")
    st.code(
        "cd /workspace/week06_slam_localization\n"
        "source /opt/ros/jazzy/setup.bash\n"
        "export ROS_DOMAIN_ID=26\n"
        "mkdir -p runtime/maps/mission1\n"
        "ros2 run nav2_map_server map_saver_cli -f runtime/maps/mission1/map\n"
        "python3 scripts/analyze_map.py --yaml runtime/maps/mission1/map.yaml "
        "--strategy perimeter_then_interior --duration-min 7 "
        "--output runtime/maps/mission1/evidence.json",
        language="bash",
    )
    st.caption("A successful analysis writes `runtime/maps/mission1/evidence.json`. You will compare its measurements with Mission 2 after both maps are saved.")
    st.write("To save visual evidence, make RViz visible in the virtual desktop, then run the next command in a terminal. You have four seconds to switch back to RViz before it captures the desktop. Inspect the image afterward and repeat if the terminal covered the map.")
    st.code("cd /workspace/week06_slam_localization\npython3 scripts/capture_desktop.py --output runtime/maps/mission1/rviz.png --delay 4", language="bash")
    local_evidence, local_yaml, local_image = runtime_map("mission1")
    evidence_item, yaml_item, image_item = local_evidence, local_yaml, local_image
    st.button("Check saved map files", key="m1.refresh")
    saved_screens = sorted((submission_root() / "mission_1").glob("rviz_screenshot.*"))
    screenshot = (artifact(None, ROOT / "runtime/maps/mission1/rviz.png")
                  or (artifact(None, saved_screens[0]) if saved_screens else None))
    evidence = load_json(evidence_item)
    metrics, error = validate_map_bundle(evidence, yaml_item, image_item)
    if error:
        st.info(error)
    else:
        st.success("The map YAML, PGM, and analysis JSON agree.")
        st.dataframe([{"measure": key, "value": value} for key, value in metrics.items()], hide_index=True)
        show_map(st, image_item, "First mapping run")
        with st.expander("How to interpret these map measures"):
            st.write("Known fraction is the share labeled free or occupied. It is not proof that labels are correct. Speckle fraction counts small isolated occupied components. Border contact can suggest a clipped map. The quality score combines these measures for discussion, not as ground truth.")
    if screenshot is None:
        st.info("Save an RViz screenshot showing the map, scan, and robot as `runtime/maps/mission1/rviz.png`, then check saved files again.")

    st.subheader("4. Explain the map in two answers")
    text_response(st, "mission_1.limitations", "Point to an area that remained unknown or poorly outlined when you stopped. Where is it in your RViz screenshot, and how did your route or the LiDAR's line of sight leave that gap?")
    text_response(st, "mission_1.drift_and_revisit", "When you returned to an area you had already scanned, did the new scan line up with its mapped walls? Did an old wall visibly shift or double? Describe what you saw. If you cannot tell whether SLAM corrected drift, say what evidence is missing rather than claiming a loop closure.")
    check = evaluate(evidence if metrics is not None else None, st.session_state["responses"], metrics is not None, metrics is not None)
    render_check(st, check)
    if st.button("Check and save Mission 1", type="primary", disabled=not check.passed or screenshot is None):
        prior = st.session_state["evidence"].get("mission_1")
        st.session_state["evidence"]["mission_1"] = evidence
        signature = current_signature(st, "mission_1")
        try:
            save_mission(
                "mission_1", {"analysis": evidence, "state_signature": signature},
                st.session_state["responses"],
                {
                    "analysis.json": evidence_item, "map.yaml": yaml_item, "map.pgm": image_item,
                    "rviz_screenshot" + Path(screenshot.name).suffix.lower(): screenshot,
                },
                state_signature=signature,
            )
        except (OSError, ValueError) as failure:
            if prior is None: st.session_state["evidence"].pop("mission_1", None)
            else: st.session_state["evidence"]["mission_1"] = prior
            st.error(f"Mission files were not saved: {failure}")
        else:
            complete_mission(st, "mission_1", signature)
            st.success("Mission 1 evidence and explanations saved.")
