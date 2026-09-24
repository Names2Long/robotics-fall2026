# Week 4 Lab Development Context

## Purpose

This is an individual, self-contained Streamlit lab about PID control and odometry. ROS 2 and Docker are not required for students. The guide teaches concepts through interactive visual demonstrations before students complete three increasingly integrated missions.

## Entry points

- Streamlit guide: `app.py`
- Simulation library: `sim_core.py`
- Windows launcher: `run_lab.ps1`
- macOS/Linux launcher: `run_lab.sh`
- Pinned local dependencies: `requirements.txt`
- Regression tests: `tests/test_lab4.py`
- Student output: `student_submission/`

The repository copy of `student_submission/` must contain only `.gitkeep`.

## Student flow

1. Introduction
2. Environment check
3. Feedback and controller concepts
4. PID playground
5. Odometry walkthrough
6. Mission 1: tune a two-link arm
7. Mission 2: calibrate forward and sideways odometry pods
8. Mission 3: plan and tune a pedestrian-aware delivery route
9. Final reflection and submission

The student cannot bypass the normal sequence. Password-protected instructor controls provide page and mission overrides for testing.

## Mission requirements

- **Mission 1:** make a prediction, tune both arm joints, hold all three poses, compare the evidence with the prediction, and save the validated result.
- **Mission 2:** predict the effect of scale error, calibrate both odometry pods, complete the multi-direction test with maximum error below 3.0 inches, analyze the evidence, and save the validated result.
- **Mission 3:** predict the route behavior, draw a route or enter coordinates, visit all four waypoints in order, maintain the required pedestrian clearance, meet mean and maximum tracking-error limits, complete the technical and human-centered analysis, and save the validated result.

Mission results are validated in Python from their evidence. A client-side `passed` value alone cannot unlock progress. If relevant activity evidence changes after a pass, that mission and later missions are invalidated and must be checked again.

## Saving, recovery, and submission

Written responses, progress, compact results, parameters, metrics, and generated evidence are autosaved with a versioned schema. Compatible data are restored in a new session. Atomic writes reduce the chance of a partial autosave, and write or recovery failures are visible in the sidebar.

The final submission cannot be saved until all missions pass, required evidence and responses are present, the reflection is between 1 and 300 words, and the student provides a name plus student ID or email. Mission and final submissions include a versioned `manifest.json` that inventories the saved files.

## Interactive components

Custom components provide the PID concept activity, PID playground, arm activity, odometry activities, and waypoint mission. Static lesson pages are embedded with `st.iframe` rather than the deprecated `components.html` call. Mission 3 also provides keyboard-friendly coordinate entry as an alternative to pointer drawing.

## Verification

From the repository root, run:

```bash
python -m unittest discover -s week04_pid_odometry/tests -v
python week04_pid_odometry/app.py --preflight
python week04_pid_odometry/app.py --smoke-test
```

The regression suite checks validators, route parsing, the final manifest, every page and mission render, removal of the student skip button, final-save gating, and autosave recovery. The smoke test asserts expected numerical ranges instead of only checking that simulations execute.
