# Instructor notes: Week 6

## Intent and teaching sequence

This lab asks students to investigate SLAM and mapping, not implement the underlying algorithm. Three tutorials bridge from dead reckoning in Lab 4 to LiDAR evidence and occupancy-grid interpretation. Students make a route prediction before each mapping run, then revise their understanding using measured and visual evidence.

Mission 1 makes the first map. Mission 2 compares a different exploration route in the same TurtleBot3 House world. The lab ends with a synthesis and reflection. The former AMCL localization mission and its two tutorials are preserved in [the future-lab module](../../future_lab_modules/localization_from_saved_map/README.md), not assigned here.

## Timing to pilot

Pilot both mapping runs with a student unfamiliar with TurtleBot3 House. Allow time for ROS startup, teleoperation, map saving, comparison, and final writing. The larger world can take longer to explore than the former TurtleBot3 World.

## Experimental controls and interpretation

Keep the world, robot, map settings, and start position the same. Stop the first mapping launch and run `bash scripts/reset_mapping.sh` before starting the second one. This closes any Gazebo process left behind after Ctrl+C. Route choice should be the main planned change. Students time each run from first movement until they judge the accessible space sufficiently mapped. They compare elapsed time, known area, speckles, and visible structure. Known area per minute is a rough efficiency measure, not ground truth. The composite score is a discussion aid, not a passing threshold. Inspect wall alignment, duplicated structures, unobserved rooms, and map clipping. Mission 1 asks students to describe a revisit without requiring a claim that loop closure occurred.

## Suggested assessment

- Mission 1 route prediction, map files, visual evidence, and interpretation: 40
- Mission 2 controlled comparison, timing, metrics, and visual evidence: 40
- Evidence-based final synthesis and individual reflection: 15
- Complete, inspectable artifacts: 5

Automated checks establish minimum evidence, not the quality of every causal claim. Manually inspect whether screenshots and numeric data support the student's interpretation and whether route comparisons are credible.

## Support and release checks

- Preflight verifies installed ROS components before mapping. Live topic checks occur after launching Gazebo and SLAM.
- If `/map` is absent, check `/scan`, `/odom`, TF, simulated time, and SLAM lifecycle. If map saving times out, wait for `/map` and map-server lifecycle readiness.
- Never advise a student to reset, clean, or overwrite their submission in response to a course update. Back up `student_submission/`, inspect `git status`, and preserve their commit.
- Pilot both mapping runs in the shared container. Verify map-pair validation, screenshots in the shared runtime folder, browser restart, old-save migration, readiness, ZIP contents, and a personal-fork Git commit.
