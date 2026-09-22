"""Five visual introductions, with progress stored alongside student responses."""
from __future__ import annotations

import inspect
import json
import math
from pathlib import Path
import uuid

from lab.evidence import frame_snapshot
from lab.navigation import set_stage
from simulation.walkthroughs import forward_command, motion_samples

TITLES = (
    "The TurtleBot motion interface", "How two wheels produce motion",
    "Robot and sensor coordinate frames", "Predict, run, and measure",
    "AI-assisted programming",
)
ASSET = Path(__file__).resolve().parents[1] / "assets" / "walkthrough.html"


def visual(st, **payload):
    import streamlit.components.v1 as components
    components.html(ASSET.read_text(encoding="utf-8").replace(
        "__PAYLOAD__", json.dumps(payload).replace("<", "\\u003c")), height=450)


def record(st, item):
    progress = st.session_state["responses"].setdefault("walkthrough.runs", [])
    if item not in progress:
        progress.append(item)


def run(st, label, key, v, w, duration=3.0, scale=1.0):
    if st.button(label, key=key):
        record(st, key)
        st.session_state["walkthrough.animation"] = {
            "samples": motion_samples(v * scale, w * scale, duration), "v": v * scale,
            "w": w * scale, "duration": duration, "token": uuid.uuid4().hex,
            "owner": st.session_state["walkthrough.index"],
        }


def animation(st):
    payload = st.session_state.get("walkthrough.animation", {})
    if payload.get("owner") != st.session_state["walkthrough.index"]:
        payload = {"samples": motion_samples(0, 0, 0), "duration": 0, "v": 0, "w": 0}
    visual(st, mode="motion", **payload)


def interface(st):
    st.write("How can two numbers tell a robot to drive, turn, or stop?")
    st.markdown("**Gazebo** is the simulated environment. **TurtleBot3** is the two-wheeled robot inside it. "
                "**ROS 2** carries messages between programs. A **Twist** message describes velocity: "
                "`linear.x` is forward speed in meters per second and `angular.z` is turning speed in radians per second.")
    st.info("Before each run, picture the path. Then watch the forward arrow and trail. "
            "These browser runs use an ideal motion model. They do not move Gazebo.")
    st.write("Positive forward speed moves toward the arrow. Negative speed reverses. Positive turning speed "
             "turns left when viewed from above, and negative turning speed turns right.")
    for label, key, v, w in (
        ("Run forward: v = 0.20, omega = 0", "forward", .2, 0),
        ("Run turn: v = 0, omega = 0.50", "turn", 0, .5),
        ("Run arc: v = 0.20, omega = 0.50", "arc", .2, .5),
        ("Run stop: v = 0, omega = 0", "stop", 0, 0),
    ):
        run(st, label, key, v, w)
    with st.expander("Try the signs"):
        v = st.slider("Forward speed (m/s)", -.2, .2, -.1, .01)
        w = st.slider("Turning speed (rad/s)", -.8, .8, -.5, .05)
        run(st, "Run these signed speeds", "signed", v, w)
    animation(st)
    st.markdown("**Stopping:** a message with both values zero requests a stop. If code exits without it, the "
                "receiving system may continue using the most recent command. The course guard is a course-provided "
                "ROS node that checks student speeds, forwards acceptable commands, and requests a stop after about "
                "0.5 seconds without a fresh command. Student code must still deliberately send a final stop.")
    with st.expander("Connect the diagram to the live robot"):
        st.write("After environment preflight, launch the lab in a virtual desktop terminal. Leave it running "
                 "and use a second terminal for inspection. Gazebo displays the robot and RViz displays ROS data.")
        st.code("cd /workspace/week03_motion_frames_ai\nbash scripts/launch_lab.sh", language="bash")
        st.code("source /opt/ros/jazzy/setup.bash\nsource /workspace/week03_motion_frames_ai/ros2_ws/install/setup.bash\n"
                "export ROS_DOMAIN_ID=25\nros2 topic info /student_cmd_vel\n"
                "ros2 interface show geometry_msgs/msg/Twist", language="bash")
        st.write("Find the linear and angular fields. The guard receives `/student_cmd_vel` and forwards "
                 "bounded commands to `/cmd_vel`. Mission 1 executes measured motion trials.")
    return ["forward", "turn", "arc", "stop"]


def wheels(st):
    st.write("Walkthrough 1 described the motion of the whole robot with forward speed and turning speed.")
    st.markdown("A differential-drive robot cannot directly actuate those two values. It has a **left wheel** and "
                "a **right wheel**. A controller converts the requested robot motion into one speed for each wheel. "
                "Looking at wheel speeds explains why the body follows a particular path.")
    st.markdown("Let $v_L$ be left-wheel linear speed, $v_R$ be right-wheel linear speed, and $L$ be the distance "
                "between the wheels. This demonstration uses $L=0.16$ m and assumes both wheels grip the floor.")
    st.latex(r"v=\frac{v_R+v_L}{2}")
    st.write("The average of the wheel speeds is the forward speed of the robot body.")
    st.latex(r"\omega=\frac{v_R-v_L}{L}")
    st.write("The wheel-speed difference creates turning. A positive result turns left. A negative result turns right.")
    st.info("Worked example: if the left wheel moves at 0.04 m/s and the right wheel at 0.16 m/s, "
            "then v = 0.10 m/s and omega = 0.75 rad/s. The robot moves forward while curving left.")
    examples = (
        ("Equal forward speeds", "equal", .12, .12, "straight"),
        ("Right wheel faster", "left_turn", .04, .16, "left curve"),
        ("Left wheel faster", "right_turn", .16, .04, "right curve"),
        ("Equal and opposite", "opposite", -.06, .06, "rotation in place"),
    )
    for label, key, left, right, path in examples:
        v, w = (right + left) / 2, (right - left) / .16
        st.caption(f"{label}: vL = {left:.2f} m/s, vR = {right:.2f} m/s, "
                   f"v = {v:.2f} m/s, omega = {w:.2f} rad/s. Predicted path: {path}.")
        run(st, f"Run: {label}", key, v, w)
    with st.expander("Choose your own wheel speeds"):
        left = st.slider("Left wheel vL (m/s)", -.16, .16, .08, .01)
        right = st.slider("Right wheel vR (m/s)", -.16, .16, .12, .01)
        st.write(f"Calculated body command: v = {(right+left)/2:.2f} m/s, omega = {(right-left)/.16:.2f} rad/s")
        run(st, "Run these wheel speeds", "custom_wheels", (right + left) / 2, (right - left) / .16)
    animation(st)
    st.write("Watch the wheel stripes. Equal speeds produce a straight trail. The robot turns toward the slower wheel. "
             "Equal and opposite speeds rotate the body without forward translation.")
    with st.expander("Under the hood: converting a robot command into wheel speeds"):
        st.write("The formulas above answer: what will the robot do for two known wheel speeds? A controller must "
                 "solve the opposite problem: what wheel speeds produce a requested forward speed and turn rate? "
                 "This reverse calculation is called inverse kinematics.")
        st.latex(r"v_R=v+\frac{\omega L}{2},\qquad v_L=v-\frac{\omega L}{2}")
        st.write("The turning contribution is added to the outside wheel and subtracted from the inside wheel. "
                 "If omega is zero, both wheels receive v. If v is zero, the wheels receive equal and opposite speeds.")
        st.markdown(r"""- Straight: $v=0.12$ m/s and $\omega=0$ gives $v_L=v_R=0.12$ m/s.
- Left turn: $v=0.10$ m/s and $\omega=0.50$ rad/s gives $v_L=0.06$ m/s and $v_R=0.14$ m/s.
- Rotate in place: $v=0$ and $\omega=0.50$ rad/s gives $v_L=-0.04$ m/s and $v_R=0.04$ m/s.""")
        st.caption("You will command v and omega in this lab. The robot controller performs this wheel conversion.")
    return ["equal", "left_turn", "right_turn", "opposite"]


def _reference_robot_snapshot():
    return {"source": "reference", "transforms": {
        "base_scan_to_base_link": {"translation": {"x": .20, "y": 0., "z": .14}, "yaw": 0.},
        "rear_camera_to_base_link": {"translation": {"x": -.18, "y": 0., "z": .22}, "yaw": math.pi},
    }}


def _frame_table(st, snapshot):
    rows = []
    for key, label in (("base_scan_to_base_link", "LiDAR described in base_link"),
                       ("rear_camera_to_base_link", "Rear camera described in base_link")):
        transform = snapshot.get("transforms", {}).get(key)
        if not transform:
            continue
        t = transform["translation"]
        rows.append({"Relationship": label,
                     "Translation (m)": f"x={t['x']:.2f}, y={t['y']:.2f}, z={t['z']:.2f}",
                     "Rotation (rad)": f"yaw={transform['yaw']:.2f}",
                     "Meaning": "sensor mounting position and orientation relative to the robot body"})
    if not rows:
        return False
    st.table(rows)
    st.write("The LiDAR faces the same direction as the body. The rear camera sits behind the body origin and "
             "its yaw is about pi radians, so its forward axis points toward the back of the robot.")
    with st.expander("View raw snapshot data"):
        st.json(snapshot)
    return True


def frames(st):
    st.write("How can one physical object have several correct coordinate descriptions?")
    st.markdown("A **coordinate frame** supplies an origin and axis directions. `base_link` is attached to the robot "
                "body, `base_scan` is attached to the LiDAR, and `rear_camera_link` is attached to a camera on the back. "
                "Because the sensors are mounted in different places and orientations, the same object has different "
                "numbers in each frame.")
    target_x = st.slider("Object x in base_link (m)", -1.5, 1.5, .8, .1)
    target_y = st.slider("Object y in base_link (m)", -1.5, 1.5, .4, .1)
    scan, camera = (target_x - .20, target_y), (-(target_x + .18), -target_y)
    visual(st, mode="robot_frames", target_x=target_x, target_y=target_y)
    st.table([
        {"Frame": "base_link", "x (m)": target_x, "y (m)": target_y, "Interpretation": "relative to robot center"},
        {"Frame": "base_scan", "x (m)": scan[0], "y (m)": scan[1], "Interpretation": "relative to forward-facing LiDAR"},
        {"Frame": "rear_camera_link", "x (m)": camera[0], "y (m)": camera[1], "Interpretation": "relative to backward-facing camera"},
    ])
    st.info("Move the object to the front and then behind the robot. A positive x value means forward along "
            "the axes of the selected frame, not one universal direction.")
    positions = st.session_state.setdefault("walkthrough.robot_frame_targets", [])
    if [target_x, target_y] not in positions:
        positions.append([target_x, target_y])
    if len(positions) > 1:
        record(st, "frames_compared")
    st.subheader("What is a transform?")
    st.write("A transform describes the translation and rotation needed to relate one frame to another. Translation "
             "describes the offset between origins. Rotation describes how the axes are oriented. ROS stores connected "
             "transforms as a frame tree. `tf2_ros` is the ROS 2 library and tool collection that publishes, stores, "
             "inspects, and applies these relationships.")
    with st.expander("Inspect the live transforms", expanded=True):
        st.write("Use the second terminal prepared in Walkthrough 1 while the simulator is running. Run each command "
                 "separately and press Ctrl+C after observing several lines.")
        st.code("ros2 run tf2_ros tf2_echo base_link base_scan", language="bash")
        st.write("This asks where `base_scan` is and how its axes are oriented when described using `base_link`. "
                 "The translation is the LiDAR mounting offset. Its rotation is close to zero because it faces forward.")
        st.code("ros2 run tf2_ros tf2_echo base_link rear_camera_link", language="bash")
        st.write("This asks the same question about the rear camera. Its x translation is negative because it is behind "
                 "the body origin. Its yaw is about pi radians because it faces backward. The values remain constant "
                 "while the robot moves because both sensors are rigidly attached to it.")
        st.code("export WEEK03_EVIDENCE_DIR=/workspace/week03_motion_frames_ai/runtime/evidence\n"
                "ros2 run course_motion_tools frame_probe", language="bash")
        st.write("The final command saves both relationships so the guide can load and explain them.")
        if st.button("Load and explain saved snapshot"):
            snapshot = frame_snapshot()
            if snapshot and _frame_table(st, snapshot):
                st.session_state["walkthrough.frame_snapshot"] = snapshot
                record(st, "frame_snapshot_explained")
                st.rerun()
            else:
                st.warning("No compatible snapshot was found. Run frame_probe after rebuilding and launching the updated lab.")
        if st.button("Use reference snapshot for this walkthrough"):
            st.session_state["walkthrough.frame_snapshot"] = _reference_robot_snapshot()
            record(st, "frame_snapshot_explained")
            st.rerun()
        selected = st.session_state.get("walkthrough.frame_snapshot")
        if selected:
            st.success(f"Loaded {selected.get('source', 'saved')} frame evidence.")
            _frame_table(st, selected)
    return ["frames_compared", "frame_snapshot_explained"]


def measure(st):
    st.write("How far should the robot travel, and what does a difference between prediction and observation tell us?")
    st.subheader("1. Straight motion")
    st.latex(r"d=vt")
    st.write("Here d is signed displacement in meters, v is constant forward speed in meters per second, and t is "
             "time in seconds. At v = 0.20 m/s for t = 5 s, d = 1.00 m.")
    st.subheader("2. Rotation")
    st.latex(r"\Delta\theta=\omega t")
    st.write("Heading change is turning speed multiplied by time. At omega = 0.50 rad/s for pi seconds, "
             "the heading changes by pi/2 radians, which is one quarter turn. This is orientation, not distance.")
    st.subheader("3. Curved motion")
    st.latex(r"R=\frac{v}{\omega}\quad(\omega\ne0)")
    st.write("R is the signed radius of a constant curve. At v = 0.20 m/s and omega = 0.50 rad/s, the radius is "
             "0.40 m. Increasing v with the same omega widens the curve. Increasing the magnitude of omega with the "
             "same v tightens it. The sign of omega selects left or right. When omega is zero, the path is straight.")
    st.caption("For an arc, |v|t is path length along the curve. It is not generally the straight-line distance "
               "between start and end. These formulas assume constant commanded velocities.")
    st.write("Start at (0 m, 0 m), heading 0 radians toward +x. Command v = 0.20 m/s, omega = 0 for 5 s.")
    run(st, "Run ideal mathematical prediction", "ideal_measure", .2, 0, 5)
    st.info("The next run deliberately applies 92 percent of the requested speed. It creates a known difference so "
            "you can practice comparing prediction with observation. It is not a model of a particular TurtleBot error.")
    run(st, "Run deliberately different observation", "changed_measure", .2, 0, 5, .92)
    animation(st)
    st.table([{"Command": "0.20 m/s for 5 s", "Prediction": "x = 1.00 m",
               "Deliberate observation": "x = 0.92 m", "Difference": "observation minus prediction = -0.08 m",
               "Known cause": "the example applied 92% speed"}])
    st.write("A live discrepancy does not identify its own cause. Command timing, acceleration, wheel slip, and the pose "
             "estimate can all contribute. Record prediction and observation, then collect additional evidence.")
    return ["ideal_measure", "changed_measure"]


ORIGINAL = '''import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

rclpy.init()
node = Node("forward_example")
pub = node.create_publisher(Twist, "/cmd_vel", 10)
msg = Twist()
msg.linear.x = 0.2
pub.publish(msg)
time.sleep(3)
pub.publish(Twist())
node.destroy_node()
rclpy.shutdown()'''


def ai(st):
    st.write("Why use an AI assistant, and what evidence is still the developer's responsibility?")
    st.markdown("AI assistants can help with ROS node structure, syntax and API usage, candidate movement logic, "
                "debugging suggestions, and test ideas. Their output is a proposed implementation. It is not proof "
                "that the robot behaves correctly.")
    st.subheader("The course command path")
    st.code("student node  ->  /student_cmd_vel  ->  course guard  ->  /cmd_vel  ->  robot", language="text")
    st.write("The course guard is a course-provided ROS node. It checks student speed limits, forwards acceptable "
             "commands, and sends a stop after about 0.5 seconds without a fresh command. It is an additional safety "
             "layer. It cannot correct the wrong direction, wrong timing, wrong frame, or an unsafe plan. Student code "
             "must still send a deliberate final zero command and handle interruption.")
    st.subheader("How this course uses AI-assisted programming")
    st.code("specify -> generate -> inspect -> predict -> test -> measure -> revise", language="text")
    st.markdown("**Before running:** specify intended behavior, preserve the original output, inspect assumptions, predict "
                "the path, and check speeds and stopping.\n\n"
                "**After running:** measure what happened, compare it with the prediction, explain discrepancies, revise, "
                "and retest. Documentation must distinguish AI output, human revisions, and collected evidence.")
    left, right = st.columns(2)
    with left:
        st.markdown("**Technical problems**\n\n- wrong sign for omega\n- degrees instead of radians\n"
                    "- wrong coordinate frame\n- incorrect timing\n- wrong topic or message type")
    with right:
        st.markdown("**Safety and responsibility problems**\n\n- unsafe velocity\n- no final stop command\n"
                    "- exception leaves motion active\n- assumes the path is empty\n- behavior is difficult to explain")
    st.subheader("Inspect a proposed implementation")
    st.write("Specification: move forward at 0.20 m/s for 3 s, stay within course limits, and stop.")
    st.code("Write a ROS 2 Python node that moves the TurtleBot forward for three seconds and then stops.", language="text")
    st.caption("This is an instructor-authored possible response. Mission 3 preserves the student's actual response.")
    st.code(ORIGINAL, language="python")
    if st.button("Inspect the proposed code"):
        record(st, "ai_inspected")
    if "ai_inspected" in st.session_state["responses"].get("walkthrough.runs", []):
        st.table([
            {"Issue": "Topic", "Finding": "It bypasses /student_cmd_vel and the course guard."},
            {"Issue": "Delivery", "Finding": "One message can be missed before publisher discovery completes."},
            {"Issue": "Timing", "Finding": "Sleeping does not prove commands were received for three seconds."},
            {"Issue": "Stopping", "Finding": "An interruption or exception can skip the final zero command."},
            {"Issue": "Validation", "Finding": "No code rejects excessive or invalid speeds and durations."},
            {"Issue": "Environment", "Finding": "It assumes the path is empty."},
            {"Issue": "Evidence", "Finding": "Running without an exception does not prove distance or stopping."},
        ])
        st.write("A useful revision separates velocity decisions from ROS communication. The decision can be tested "
                 "at exact timing boundaries, while ROS and simulator tests evaluate delivery and physical behavior.")
        st.code(inspect.getsource(forward_command), language="python")
        st.subheader("Tests establish specific claims")
        st.write("The checks below cover motion before the deadline, zero velocity at and after the deadline, excessive "
                 "speed, and invalid duration. ROS and simulator tests are still needed for delivery and physical motion.")
        if st.button("Run the decision and boundary tests"):
            record(st, "ai_tested")
        if "ai_tested" in st.session_state["responses"].get("walkthrough.runs", []):
            rows = []
            for t, expected in ((0, (.2, 0)), (2.99, (.2, 0)), (3, (0, 0)), (4, (0, 0))):
                actual = forward_command(t)
                rows.append({"Case": f"elapsed={t}", "Expected": str(expected), "Actual": str(actual), "Pass": actual == expected})
            for label, call in (("excessive speed", lambda: forward_command(0, speed=.3)),
                                ("negative duration", lambda: forward_command(0, duration=-1))):
                try:
                    call()
                except ValueError:
                    rows.append({"Case": label, "Expected": "ValueError", "Actual": "ValueError", "Pass": True})
                else:
                    rows.append({"Case": label, "Expected": "ValueError", "Actual": "accepted", "Pass": False})
            st.table(rows)
            st.success("The pure decision checks passed. They do not establish ROS delivery or physical motion.")
    st.subheader("Responsibility remains with the developer")
    st.write("The developer must inspect rather than copy the output, understand the deployed behavior, verify safety "
             "constraints and stopping, connect each test to a claim, and document AI output separately from human "
             "revisions and evidence. Using AI does not transfer responsibility for the robot's behavior.")
    return ["ai_inspected", "ai_tested"]


def render(st):
    st.title("Lab 3 guided walkthroughs")
    st.write("Explore commands, wheels, coordinates, measurements, and AI-assisted code. "
             "Reuse the course Docker environment from Lab 1 for ROS inspection.")
    index = st.session_state.setdefault("walkthrough.index", 0)
    completed = st.session_state["responses"].setdefault("walkthrough.completed", [])
    st.progress(len(completed) / 5, text=f"{len(completed)}/5 walkthroughs reviewed")
    st.session_state["walkthrough.selector"] = index

    def select():
        st.session_state["walkthrough.index"] = st.session_state["walkthrough.selector"]
        st.session_state["scroll_to_top_pending"] = True

    st.selectbox("Walkthrough", range(5), format_func=lambda i: f"{i+1}. {TITLES[i]}",
                 key="walkthrough.selector", on_change=select)
    st.header(f"{index+1}. {TITLES[index]}")
    needed = (interface, wheels, frames, measure, ai)[index](st)
    tried = st.session_state["responses"].get("walkthrough.runs", [])
    remaining = [key.replace("_", " ") for key in needed if key not in tried]
    if remaining:
        st.info("Still to try: " + ", ".join(remaining) + ". Watch each animation finish before marking reviewed.")
    if st.button("Mark reviewed", disabled=bool(remaining)):
        if index not in completed:
            completed.append(index)
        st.rerun()
    if index in completed:
        st.success("Walkthrough reviewed. You can revisit any example.")
    previous, next_column = st.columns(2)
    with previous:
        if st.button("Previous walkthrough", disabled=index == 0, use_container_width=True):
            st.session_state["walkthrough.index"] = index - 1
            st.session_state["scroll_to_top_pending"] = True
            st.rerun()
    with next_column:
        if index < 4:
            if st.button("Next walkthrough", disabled=index not in completed, type="primary", use_container_width=True):
                st.session_state["walkthrough.index"] = index + 1
                st.session_state["scroll_to_top_pending"] = True
                st.rerun()
        elif st.button("Continue to environment preflight", disabled=len(completed) != 5,
                       type="primary", use_container_width=True):
            set_stage(st, "preflight")
