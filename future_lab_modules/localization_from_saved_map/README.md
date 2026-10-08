# Deferred localization module

This folder preserves the former Lab 6 Guided Tutorials 4 and 5 and Mission 3 for a possible future lab. It is not part of the active Week 6 guide, preflight, ROS build, readiness checks, or submission. Students should not run these files from this folder as an assignment.

The module includes:

- `tutorials.py`, with the SLAM-to-localization transition and AMCL particle-belief visualization
- `pages/mission_3.py`, with four clean-start localization trials and a safety-rule critique
- `missions/mission_3.py` and `analysis/localization.py`, with evidence checks and metrics
- `scripts/launch_localization.sh`, a ROS launch file, a localization recorder, and a scan degrader
- `tests/test_localization.py`, with focused tests for the archived analysis and mission checks

The code is a preserved source module, not a standalone app. The Streamlit page still expects the Lab 6 autosave, evidence, navigation, submission, and UI helpers. The ROS launcher still expects a built `course_slam_tools` package in a lab workspace. Before assigning it in a later lab, copy or adapt those dependencies, register its pages and stages, update the lab ID and paths, rebuild the ROS package, and run an end-to-end pilot with a saved House map. In particular, do not assume that AMCL covariance is true position error. The original recorder requires a separately verified reference pose in the `map` frame for numeric position-error claims.

The old Mission 3 work remains in any existing student's saved files. Active Week 6 does not require it. If this material becomes a new assignment, provide a new submission location and recovery path rather than reusing a student's old Lab 6 files.
