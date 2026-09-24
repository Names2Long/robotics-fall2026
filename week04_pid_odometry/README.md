# Week 4: PID Control and Odometry

This is an individual, self-contained Streamlit lab. ROS 2 and Docker are not required.

Students first complete guided visual activities about feedback control, PID terms, encoders, wheel geometry, and odometry. They then complete three missions:

1. Tune PID controllers for a two-link robot arm.
2. Calibrate forward and sideways odometry pods on a holonomic robot.
3. Plan and tune a sidewalk-delivery route that meets waypoint, tracking, and pedestrian-clearance requirements.

## Start the lab

Open a terminal in the repository root. The launcher creates a Lab 4 virtual environment, installs the tested package versions, runs a preflight check, and starts Streamlit.

### Windows PowerShell

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\week04_pid_odometry\run_lab.ps1"
```

### macOS or Linux

```bash
bash week04_pid_odometry/run_lab.sh
```

Open the URL printed by Streamlit, normally <http://localhost:8501>.

The first page of the guide includes an environment check. Do not begin the tutorial until every check passes.

## Manual setup fallback

If the launcher cannot be used, create and activate a Python 3.12 virtual environment, then run these commands from the repository root:

```bash
python -m pip install -r week04_pid_odometry/requirements.txt
python week04_pid_odometry/app.py --preflight
python -m streamlit run week04_pid_odometry/app.py
```

On Windows, the virtual-environment Python is usually `.venv\Scripts\python.exe`. On macOS and Linux it is usually `.venv/bin/python`.

## Saving and recovery

The guide automatically saves written responses, mission state, compact run results, and generated GIF evidence under:

```text
week04_pid_odometry/student_submission/
```

If the browser, Streamlit, or the computer closes, start the lab again with the same launcher. Compatible saved work is restored automatically, and the sidebar reports what was recovered.

Changing a controller, calibration, route, or other relevant result after a mission check invalidates that check. Run the mission check again before submitting.

## Student workflow

1. Run the environment check.
2. Complete every guided tutorial section in order.
3. Write each prediction before opening its mission activity.
4. Run the activity, inspect the measured result, and compare it with the prediction.
5. Use each mission checklist to identify any unfinished requirement.
6. Save each passed mission to unlock the next mission.
7. Complete the final reflection and submission-readiness checklist.
8. Save the complete submission folder.

## Submission

The final submission contains structured JSON, CSV evidence, written explanations, the individual reflection, GIF evidence when available, and a versioned `manifest.json`.

From the repository root, commit only after the final readiness table reports that every requirement is ready:

```bash
git add week04_pid_odometry/student_submission
git commit -m "Submit Week 4 PID and odometry lab"
git push
```

Submit the URL of that individual Git commit. Do not submit only a screenshot or a link to the repository homepage.

## Updating before beginning

Follow the repository update procedure in [`ROS_DOCKER_SETUP.md`](../ROS_DOCKER_SETUP.md), even though this particular lab does not use ROS or Docker. Always commit existing work before merging course updates.

## Instructor verification

Run the automated checks from the repository root:

```bash
python -m unittest discover -s week04_pid_odometry/tests -v
python week04_pid_odometry/app.py --smoke-test
```

Instructor controls in the sidebar can jump to tutorial pages or missions without changing the normal student sequence.
