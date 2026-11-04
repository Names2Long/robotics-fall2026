# Instructor release checks

Use a dedicated WEEK09_SUBMISSION_DIR and runtime/release_trials for instructor testing. Never put synthetic successful results in the default student folder.

Check these separately:

1. Unit and app tests. All pages render, source changes invalidate old results, empty evidence cannot pass, autosave backup recovery preserves text, and exports contain file hashes.
2. Offline student workers. Test valid paths, invalid paths, missing implementations, unreachable goals, expansion limits and a hard process timeout. Search functions must call ctx.expand.
3. Build the ROS workspace and run course_preflight.sh in the course container.
4. Execute the Nav2 baseline and an external path on both maps. Confirm active lifecycle nodes, map-frame localization, live lidar, motion, bounded execution and an evidence file.
5. Test social baseline and both field configurations. Confirm person geometry, radii, timestamped exposure and explicit local-minimum or oscillation outcomes.
6. Inspect unsuccessful results and startup logs. Environment failures must never count as planner evidence. Do not interpret a stationary failure as socially superior.
7. Before handing off, archive instructor runtime reports outside runtime/trials and preserve any real student work. Launch a fresh app session and confirm Welcome.

A complete class experiment can take longer than a smoke test. Report exactly which actual robot combinations have been exercised. A passing pure-Python test is not proof of ROS integration or real-world safety.

Protocol 7 uses private Gazebo partitions and complete process-group cleanup. Verify that only the current simulator remains between attempts and that none remains after the batch. Destination acceptance is position-only, with the same 0.25 m tolerance across planners. Repeats remain recommended rather than required. An execution timeout or search-resource limit can be a valid comparison outcome, but a lifecycle/setup error cannot complete a mission. See RELEASE_TESTING.md for the complete isolated release run and submission-export checks.

Legacy scaffold tools remain for compatibility. They are not the current assignment. The current social intervention is potential-field path refinement, not a keepout-mask assignment.

