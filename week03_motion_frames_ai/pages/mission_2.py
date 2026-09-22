from __future__ import annotations
import math
from pathlib import Path

from lab.camera_ai import load_lock,lock_original
from lab.evidence import camera_evaluation,evidence_id,frame_snapshot
from lab.frame_learning import reference_snapshot,valid_snapshot
from lab.navigation import set_stage
from lab.session import complete_mission,response,set_response
from lab.submissions import save_mission,snapshot_camera_source
from lab.ui import render_check
from missions.mission_2 import evaluate,current_hash

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"ros2_ws/src/week03_camera_transform/week03_camera_transform/camera_transform.py"


def answer(st,key,label,height=120):
    full=f"mission_2.{key}";widget=f"m2.{key}"
    if widget not in st.session_state: st.session_state[widget]=str(response(st,full,""))
    value=st.text_area(label,key=widget,height=height);set_response(st,full,value);return value


def snapshot_table(st,snapshot):
    rows=[]
    for key,label in (("base_scan_to_base_link","LiDAR relative to robot body"),
                      ("rear_camera_to_base_link","Rear camera relative to robot body"),
                      ("hall_camera_to_base_link","Fixed hallway camera relative to robot body")):
        item=snapshot["transforms"][key];t=item["translation"]
        rows.append({"Relationship":label,"x (m)":round(t["x"],3),"y (m)":round(t["y"],3),
                     "z (m)":round(t["z"],3),"yaw (rad)":round(item["yaw"],3)})
    st.table(rows)


def render(st):
    st.title("Mission 2: Transform a hallway-camera observation")
    st.write("Use the frame relationships introduced in Walkthrough 3, then use an AI assistant to help implement and test a ROS 2 transformation from a fixed environmental camera to the moving robot body.")

    st.header("Part A: Reuse the frame evidence")
    st.write("You already inspected `base_link`, `base_scan`, and `rear_camera_link` in Walkthrough 3. You do not need to repeat `tf2_echo`. This mission adds `hall_camera`, a fixed camera visible in Gazebo.")
    st.info("ROS connects the fixed camera and moving robot through `odom`. Here, odom is a reference frame containing an estimate of robot motion from a starting point. That estimate can drift. The next lab examines odometry in detail. For this mission, you only need to know that the frame tree uses it to connect the fixed camera to `base_link`.")
    current=response(st,"mission_2.snapshot",{})
    if not valid_snapshot(current):
        candidate=frame_snapshot();candidate=dict(candidate) if isinstance(candidate,dict) else {};candidate["source"]="live"
        walkthrough=st.session_state.get("walkthrough.frame_snapshot",{})
        if valid_snapshot(candidate): current=candidate;set_response(st,"mission_2.snapshot",current)
        elif valid_snapshot(walkthrough): current=walkthrough;set_response(st,"mission_2.snapshot",current)
    left,right=st.columns(2)
    with left:
        if st.button("Load latest saved frame snapshot",use_container_width=True):
            candidate=frame_snapshot();candidate=dict(candidate) if isinstance(candidate,dict) else {};candidate["source"]="live"
            if valid_snapshot(candidate): set_response(st,"mission_2.snapshot",candidate);st.rerun()
            st.warning("No compatible live snapshot was found. Rebuild and relaunch the lab, then rerun frame_probe in Walkthrough 3.")
    with right:
        if st.button("Use reference frame evidence",use_container_width=True): set_response(st,"mission_2.snapshot",reference_snapshot());st.rerun()
    snapshot=response(st,"mission_2.snapshot",{})
    if valid_snapshot(snapshot):
        st.success(f"Using {snapshot['source']} frame evidence captured or created at {snapshot['captured_at']}.")
        snapshot_table(st,snapshot)
        st.write("The two robot-mounted sensor relationships remain fixed. The hallway-camera relationship changes as the robot moves because the camera remains in the environment while `base_link` moves.")
    else: st.warning("Select live or reference frame evidence before saving this mission.")
    answer(st,"frame_context","Explain why the rear-camera transform stays fixed while the hallway-camera-to-base_link transform changes as the robot moves.")

    st.header("Part B: Preserve an underspecified AI attempt")
    lock=load_lock()
    vague="Write ROS 2 Python code that converts a point detected by the hallway camera into the robot's base_link frame."
    st.write("Use an AI assistant of your choice with this short prompt. It deliberately leaves out important details so you can inspect the assumptions in the response.")
    st.code(vague,language="text")
    if not lock:
        prompt=answer(st,"initial_prompt","Paste the exact prompt you used",100)
        output=answer(st,"initial_output","Paste the complete original AI response without editing it",190)
        source=answer(st,"initial_source","Paste the original Python code without Markdown fences",190)
        if st.button("Preserve initial AI response",disabled=not all(value.strip() for value in (prompt,output,source))):
            try: lock_original(prompt,output,source)
            except (OSError,ValueError,FileExistsError) as error: st.error(f"Could not preserve the response: {error}");return
            st.rerun()
        st.info("Preserve the original response before revising any code.");return
    if not lock.get("integrity_valid"):
        st.error("The preserved Mission 2 AI record is missing or changed. Restore it from your saved copy before continuing.");return
    st.success(f"Initial AI response preserved at {lock['locked_at']}.")
    answer(st,"initial_analysis","Inspect the first response. Identify assumptions or omissions involving source and target frames, PointStamped metadata, timestamps, the TF buffer, hard-coded offsets, unavailable transforms, or robot motion topics.",170)

    st.header("Part C: Improve the prompt, revise the program, and test it")
    st.write("The starter file fixes the function name so the course tests can evaluate many valid implementations:")
    st.code("/workspace/week03_motion_frames_ai/ros2_ws/src/week03_camera_transform/week03_camera_transform/camera_transform.py")
    improved="""This is a ROS 2 Jazzy Python project. Complete only this existing function:
transform_camera_point(tf_buffer, point: geometry_msgs.msg.PointStamped) -> PointStamped | None

Requirements:
- Accept only a point whose header.frame_id is hall_camera; otherwise raise ValueError.
- Use the supplied tf2_ros Buffer to transform the stamped point into base_link. Do not hard-code offsets.
- Import tf2_geometry_msgs so tf2_ros knows how to transform PointStamped messages.
- Preserve and use the point's timestamp so the transform corresponds to the observation.
- If the transform is unavailable, return None without commanding robot motion.
- Do not create publishers or publish to any velocity topic.
Explain the assumptions and return the complete camera_transform.py code."""
    st.write("Use this improved prompt as a follow-up or a new request:")
    st.code(improved,language="text")
    answer(st,"improved_changes","Before testing, explain how the improved prompt changes the source/target frames, timestamp handling, use of TF, and failure behavior.",150)
    st.write("Replace the `NotImplementedError` in the starter file with your reviewed implementation. Then run the course-provided tests:")
    st.code("cd /workspace/week03_motion_frames_ai\nsource /opt/ros/jazzy/setup.bash\npython3 scripts/evaluate_camera_transform.py",language="bash")
    st.write("The tests check the required function, camera source, body target, rotated coordinates, unavailable-transform behavior, and absence of robot motion publication.")
    st.write("With Gazebo and the course launch still running, verify the current TF tree and observation:")
    st.code("python3 scripts/evaluate_camera_transform.py --live",language="bash")
    result=camera_evaluation()
    if st.button("Refresh camera test evidence"): st.rerun()
    if result:
        st.table([
            {"Check":"Implementation file found","Result":"Pass" if result.get("file_present") else "Not yet"},
            {"Check":"Five course tests","Result":f"Pass ({result.get('test_count',0)})" if result.get("unit_tests_passed") else f"Not yet ({result.get('test_count',0)})"},
            {"Check":"Live hall_camera to base_link transform","Result":"Pass" if result.get("live_passed") else "Not verified"},
        ])
        with st.expander("Camera evaluator output"): st.code(result.get("unit_test_output",""))
    pending=st.checkbox("Live camera verification is pending because ROS could not complete it",value=bool(response(st,"mission_2.live_pending",False)))
    set_response(st,"mission_2.live_pending",pending)
    if pending: answer(st,"live_issue","Record the error, what you tried, and what remains unverified.")

    st.header("Part D: Explain the engineering consequence")
    answer(st,"synthesis","In one response, explain what the initial AI output assumed or got wrong, how the improved prompt changed the program, what could happen around people if the wrong transform were used, which test detects that problem, and what the robot should do when transform data is unavailable.",210)

    responses=st.session_state["responses"];check=evaluate(result,lock,responses,SOURCE);render_check(st,check)
    relevant={key:value for key,value in responses.items() if key.startswith("mission_2.")}
    current_id=evidence_id(result,lock,relevant,current_hash(SOURCE))
    if st.button("Check and save Mission 2",disabled=not check.passed,type="primary"):
        save_mission("mission_2",{"evidence_id":current_id,"snapshot":snapshot,"camera_evaluation":result,
                     "live_verification_pending":not result.get("live_passed"),"check":[item.__dict__ for item in check.requirements]},responses)
        snapshot_camera_source();complete_mission(st,"mission_2",current_id);st.rerun()
    if check.passed and st.session_state.get("checked_evidence_ids",{}).get("mission_2")==current_id:
        st.success("Mission 2 saved with frame evidence, original AI output, revised source, tests, and analysis.")
        if st.button("Continue to Mission 3",type="primary"): set_stage(st,"mission_3")
