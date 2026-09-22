# Lab 3: Motion, Frames, and AI-Assisted Programming

An individual lab: predict robot motion, interpret coordinates, and develop a tested motion program with an AI assistant. Reuse the environment from Lab 1. For installation and semester updates, see [ROS Docker setup](../ROS_DOCKER_SETUP.md).

## Start the lab

From the repository root on your computer, use Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\ros_course.ps1 lab week03_motion_frames_ai
```

Or macOS/Linux:

```bash
bash scripts/ros_course.sh lab week03_motion_frames_ai
```

Open the [guide](http://localhost:8501) and [virtual desktop](http://localhost:6080/vnc.html?autoconnect=1&resize=remote). Keep Docker running. Inside the virtual desktop, open a terminal through Applications > Shells.

## Environment check

In virtual desktop terminal A:

```bash
cd /workspace/week03_motion_frames_ai
bash scripts/course_preflight.sh --setup
bash scripts/launch_lab.sh
```

The first command builds and checks dependencies. Leave the launch command running. Once Gazebo is ready, open terminal B:

```bash
cd /workspace/week03_motion_frames_ai
bash scripts/course_preflight.sh
```

Alternatively select **Run live preflight checks** in the guide. Checks cover packages, ROS domain 25, writable evidence storage, simulation clock, odometry, command guard, and transforms. A setup-only check does not establish that the simulator is running.

## Learning sequence

1. Five visual walkthroughs introduce commands, wheels, frames, prediction/measurement, and AI code review. Try the examples and mark each reviewed.
2. Mission 1: predict straight motion, turn-then-drive, and an arc in radians. Draw the turn-then-drive path in the guide, run and analyze each trial, compare all three, and evaluate motion in a public hallway.
3. Mission 2: reuse robot/sensor frame evidence, preserve and inspect an underspecified AI response, revise a hallway-camera-to-robot transform, and run five supplied tests.
4. Mission 3: save a specification before prompting, preserve original AI response and code, review and revise the implementation, and test it.
5. Write a 100 to 150 word technical synthesis and the standardized [personal reflection](../FINAL_REFLECTION.md) of 1 to 300 words.

## Mission 2 camera-transform files and commands

Preserve the first AI response in the guide. Revise `ros2_ws/src/week03_camera_transform/week03_camera_transform/camera_transform.py`, then run:

```bash
source /opt/ros/jazzy/setup.bash
cd /workspace/week03_motion_frames_ai
python3 scripts/evaluate_camera_transform.py
python3 scripts/evaluate_camera_transform.py --live
```

The first command tests the code without moving the robot. The second also checks the current `hall_camera` to `base_link` transform.

## Mission 3 files and commands

Follow the numerical pattern specification in the guide. Implement `build_pattern` in `ros2_ws/src/week03_pattern/week03_pattern/pattern.py`. Create at least two assignment-specific tests in `ros2_ws/src/week03_pattern/test/test_student_pattern.py`. The provided ROS wrapper handles publication and stopping.

From the lab folder, evaluate code without moving the robot:

```bash
python3 scripts/evaluate_ai_pattern.py
```

For a live run in terminal B, with the simulator running in A:

```bash
source /opt/ros/jazzy/setup.bash
cd /workspace/week03_motion_frames_ai/ros2_ws
colcon build --packages-select week03_pattern --symlink-install
source install/setup.bash
export ROS_DOMAIN_ID=25
cd ..
python3 scripts/run_assigned_pattern.py
```

The live runner refreshes the evaluation report after a complete run. Source or test changes require a fresh evaluation and live run. Interruption tests are recorded separately; complete another full run afterward for current live completion evidence.

## Saving and recovery

- Use each form's Save/Check button. Other fields are autosaved after their values reach the guide; **Save progress now** makes that step explicit.
- The guide restores the saved section, responses, and walkthrough progress after restart. A previous autosave copy is retained for recovery.
- Use the sidebar to revisit opened sections. After edits, check and save the affected mission again.
- If Docker pauses or the browser disconnects, copy unsent text before refreshing. Resume Docker and reconnect. Work in one guide tab.
- A failed Mission 1 run retains the prediction. Retry or select labeled modeled evidence. The model uses 92% translation and 93% rotation; these are imposed differences, not measured errors.
- Mission 2 offers labeled reference frame evidence if capture fails. Its five code tests must still pass. If the live transform cannot run, document what remains unverified.
- Mission 3 requires passing code/model tests. If ROS cannot complete, document pending live verification; the report does not claim a successful live run.
- Failed resets do not erase answers. Stop the simulator launch with Ctrl+C and relaunch before retrying live motion.

## Submit

Select **Check and save** for each mission. The final page revalidates current answers, code, and evidence. Finish both writing sections, then select **Prepare submission** and download a ZIP backup. The manifest lists evidence sources, pending verification, and file hashes.

On your computer, from the repository root:

```bash
git status
git add week03_motion_frames_ai/student_submission week03_motion_frames_ai/ros2_ws/src/week03_pattern week03_motion_frames_ai/ros2_ws/src/week03_camera_transform
git commit -m "Submit Lab 3"
git push
```

Submit the pushed commit's URL through the course submission channel and ensure the instructor has repository access. Follow instructor directions if submitting the ZIP instead. The original AI record, final source, tests, sketch, analyses, synthesis, and reflection are included. Downloads are not automatically sent to the instructor.

## Maintainer verification

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
```

Streamlit must be installed for interface tests. ROS integration also requires the running course container. The student pattern starter deliberately raises `NotImplementedError` until implemented.
