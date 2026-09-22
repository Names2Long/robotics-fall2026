# Week 1: Discovering a Robot Through ROS 2

This individual lab connects three conceptual foundations to a simulated TurtleBot3: why robotics software is difficult, how robot architectures organize sensing and action, and how ROS 2 implements modular communication. Week 1 includes the one-time setup of the shared course container, but installation troubleshooting is not the graded learning objective.

## Learning sequence

1. **Part 1 - Why robotics software is difficult:** manipulate toy examples of imperfect sensors, timing delays, distributed failures, and hardware slip.
2. **Part 2 - Robot software architectures:** watch the same scenario behave under reactive, behavior-based, deliberative, and hybrid control, then run a safety override.
3. **Part 3 - What ROS 2 provides:** follow topic messages, call a service, break graph connections, and try simulated ROS inspection commands.
4. **Preflight:** verify the shared ROS 2 Jazzy environment.
5. **Mission 1 - Observe:** learn the simulation and ROS graph vocabulary, then follow a guided tour of four nodes, key topics, and two communication paths.
6. **Mission 2 - Control:** predict and execute motion, then compare command timing and expected versus observed behavior.
7. **Mission 3 - Create behavior:** implement and test the decision functions used by a supplied LiDAR obstacle-stop ROS 2 node.
8. **Final synthesis:** connect the three parts to live evidence and the implemented behavior.

The first three parts are required, ungraded Streamlit tutorials. They contain demonstrations rather than quiz questions or written-response boxes. Exploration progress autosaves and is collected in `student_submission/foundations.md`.

## Supported environment

The recommended environment is the shared course Docker image on Windows, macOS, or Linux. It contains Ubuntu 24.04, ROS 2 Jazzy, TurtleBot3, Gazebo, RViz, colcon, and the Streamlit dependencies. Students configure it once in this lab and reuse it for Weeks 3, 6, 8, 9, and 11.

Native Ubuntu 24.04 with ROS 2 Jazzy remains a supported performance fallback. Native ROS installation on Windows and macOS is not part of the supported course workflow.

The ROS packages are deliberately separated from the Streamlit application. ROS writes machine-readable graph, timing, and behavior evidence to `runtime/evidence/`; Streamlit reads that evidence and creates the durable `student_submission/` record.

## Set up the shared ROS 2 environment

Before starting Week 1, follow the platform-specific instructions in the [Shared ROS 2 Course Environment setup guide](../ROS_DOCKER_SETUP.md). That setup is completed once and reused for every ROS-based lab.

## Run the lab after initial setup

Start or reopen Week 1 from the repository root on the host computer.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ros_course.ps1 lab week01_ros_foundations
```

Using `-ExecutionPolicy Bypass` applies only to this PowerShell process and prevents Windows from blocking the course script.

macOS/Linux:

```bash
./scripts/ros_course.sh lab week01_ros_foundations
```

After the command confirms that Week 1 has started, open both pages:

- [Week 1 lab guide](http://localhost:8501)
- [Week 1 virtual desktop](http://localhost:6080/vnc.html?autoconnect=1&resize=remote)

Inside the Week 1 terminal in the virtual desktop, verify the environment:

```bash
bash scripts/course_preflight.sh
```

When the guide directs you to start the TurtleBot simulation, run:

```bash
bash scripts/launch_lab.sh
```

The course launcher already sources ROS, selects `ROS_DOMAIN_ID=24`, sets the TurtleBot3 model, changes into the lab directory, and starts Streamlit.

## Mission 3 starter behavior

The decision file below is intentionally incomplete:

- `ros2_ws/src/week01_behavior/week01_behavior/decision.py`

Students implement the two pure decision helpers and create `test/test_student_decision.py`. The supplied `test/test_decision.py` provides additional checks. The ROS wrapper already includes parameters, a subscriber, a publisher, command bounding, and a stale-scan watchdog so students can focus on interpreting sensor data and making a safe move-or-stop decision.

Run its checks with:

```bash
bash scripts/evaluate_behavior.sh
```

The evaluator exits unsuccessfully until the student implementation passes all required safety scenarios.

## Verification for maintainers only

Students do not need to run the commands in this section. Students should follow the Streamlit guide at <http://localhost:8501>, which presents the required commands in order and explains the expected result.

The application and mission validators can be checked without ROS:

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
```

ROS integration still requires an Ubuntu/ROS environment. Validate there with:

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
colcon test
colcon test-result --verbose
```

## Submission

The app generates:

```text
student_submission/
├── student.json
├── foundations.md
├── final_reflection.md
├── autosave/
│   ├── responses.json
│   └── responses.md
├── mission_1/
│   └── ros_system_diagram.md
├── mission_2/
├── mission_3/
│   └── source/
└── manifest.json
```

An individual Git commit is a saved snapshot of one student's completed lab in that student's personal GitHub fork. It is not a separate file type. After the guide says the submission is complete, open PowerShell or Terminal on the host computer, change to the repository root, and run:

```bash
git status
git add week01_ros_foundations/student_submission week01_ros_foundations/ros2_ws/src/week01_behavior
git commit -m "Submit Week 1 ROS foundations lab"
git push origin main
```

Then open the fork on GitHub, select the new commit, and copy its URL. Submit that commit URL through the course submission system. The URL identifies the exact version being submitted and keeps the work separate from other students' submissions.

## Required final reflection

After the technical work, complete the individual [final reflection](../FINAL_REFLECTION.md). Respond to any or all of the five prompts in 1–300 words. A blank response or a response over 300 words cannot finalize the submission. The app saves the response as `student_submission/final_reflection.md`, separate from technical syntheses and mission explanations.
