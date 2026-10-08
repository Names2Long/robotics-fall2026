# Week 6: SLAM and Mapping

This individual lab uses ROS 2 Jazzy, the TurtleBot3 House simulation, SLAM Toolbox, RViz, and a Streamlit guide. Students investigate how motion and LiDAR evidence support or limit an occupancy-grid map. The AMCL localization mission has been moved to [a future-lab module](../future_lab_modules/localization_from_saved_map/README.md).

## Student path

1. Guided Tutorial 1: encoders, dead reckoning, and accumulated error.
2. Guided Tutorial 2: topological versus metric maps and occupancy-grid updates.
3. ROS preflight and Guided Tutorial 3: identify measurements, estimates, and accumulated map evidence in RViz.
4. Mission 1: predict a route, map, revisit, save, and interpret.
5. Mission 2: predict and compare a controlled second strategy.
6. Write the technical synthesis and separate individual reflection. Prepare and inspect the submission.

The guide marks original predictions before results. A prediction can be wrong and still be valuable evidence of learning. Do not edit PGM maps or evidence JSON by hand.

Lab 6 uses TurtleBot3 House for both mapping runs. Maps made in the earlier TurtleBot3 World do not match the House layout. Keep those older files as backups, then create and analyze new House maps before comparing runs.

## Start the shared course environment

From the repository root, use the one-time setup described in [ROS_DOCKER_SETUP.md](../ROS_DOCKER_SETUP.md). Then start Lab 6:

Windows:

```powershell
.\scripts\ros_course.ps1 lab week06_slam_localization
```

macOS/Linux:

```bash
./scripts/ros_course.sh lab week06_slam_localization
```

The guide opens at `http://localhost:8501`. The course launcher sets `ROS_DOMAIN_ID=26` and opens the lab directory. A new desktop terminal may not inherit that setting, so the Lab 6 launch scripts set it explicitly. On the preflight page, click **Run preflight now**. The guide runs `bash scripts/course_preflight.sh` in the shared container and ignores results from earlier launches. Guided Tutorial 3 starts mapping and RViz. Keep both running as you enter Mission 1. Do not launch a second copy. Stop the robot before switching terminals. Never run two Gazebo worlds in the same domain.

New virtual desktop terminals may open at `/workspace`, not the Lab 6 folder. Each command block in the guide begins with `cd /workspace/week06_slam_localization` so scripts and runtime files resolve correctly. The guide includes a delayed desktop capture command for RViz screenshots. Switch to RViz during the delay, then inspect the saved image before checking the mission.

If the simulator or recorder fails, preserve `student_submission/` and rerun only the missing condition. The guide reads files from `runtime/` automatically and can reopen previously saved submission artifacts. No file uploads are needed. Save RViz screenshots at the paths shown in the guide. In Mission 2, stop the first mapping launch, run `bash scripts/reset_mapping.sh`, then start a fresh world with the robot at its original pose and an empty SLAM map. The reset closes leftover Gazebo processes but does not change saved map files. Time both routes from first movement to a usable map and compare time alongside coverage and visible structure.

## What the numbers mean

Known fraction, speckles, border contact, and the composite map score help compare maps but do not establish a true geometric map error. They are discussion evidence, not passing thresholds. Use RViz and the simulated robot to judge visible structure and label uncertainty honestly.

## Submission and recovery

Prepare the submission in the guide. Its readiness table checks current mission artifacts, writing, and identity. The manifest records file hashes. Download the ZIP as a backup. In your personal fork, commit the complete `student_submission/` directory from the repository root:

```bash
git status
git add week06_slam_localization/student_submission
git commit -m "Submit Lab 6"
git push origin main
```

Open the commit on GitHub, verify that it contains your submission files, and submit its URL through the course submission system. The ZIP is a backup, not an automatic upload.

If the guide reports an unreadable autosave, do not reset or delete files. Copy `student_submission/` somewhere safe and contact the instructor. A prior valid autosave is recovered automatically when possible, with the unreadable copy preserved.

## Maintainer verification

ROS-independent tests:

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
python3 -m compileall -q app.py analysis lab missions pages ros2_ws/src/course_slam_tools/course_slam_tools
```

Full release verification must run in the course ROS 2 container. Build `ros2_ws`, run preflight, produce both maps, verify the YAML/PGM pairs and previews, restart the browser, and prepare the final ZIP. Confirm that Mission 2 leads directly to the final page and that no localization trial is required for submission.
