# Implementation verification

## Student release: protocol 7, October 29, 2026

The release uses a minimal Nav2 launch with localization, planning, path following, velocity smoothing and collision monitoring. All four managed navigation nodes must be active before motion. Unused docking, route, waypoint and behavior-tree servers are not launched. A common PositionGoalChecker uses the task's 0.25 m position tolerance without imposing an arbitrary parking orientation.

Each attempt has its own Gazebo transport partition. Cleanup sends a final termination signal to remaining process-group children even if their launcher has already exited. A real subprocess regression test verifies this case. Three old orphaned Lab 8 servers were identified and stopped before the isolated rerun. Earlier protocol 4 through 6 robot runs are preliminary records, not the release acceptance evidence.

Actual protocol-7 acceptance results:

- All 14 planner/map navigation cells were exercised with isolated simulators. Eleven journeys succeeded, constrained DFS reached the common execution timeout, and IDDFS reached its planning budget on each map. There were no environment errors. All student navigation-completion checks pass for these measured results.
- All six paired social trials succeeded with the Gazebo GUI enabled. These used A* and RRT on the open map, baseline and gains 0.05 and 0.20 with a 1.0 m influence distance and 0.08 m refinement step. All social-completion checks pass. These are test configurations, not guaranteed best settings or a claim about real people.
- The full offline comparison passes current completion checks, including the disconnected free-endpoint map. This pure-Python evidence is independent of Gazebo transport.
- The ROS package builds and all software preflight checks pass, including the PositionGoalChecker plugin. Syntax checks pass.
- Forty-two unit and app tests pass, including process cleanup, unique transport partitions, stale-source-cache prevention and ZIP-cache exclusions.
- Measured release data was loaded into an isolated temporary submission. Final app readiness, complete ZIP generation and every manifest hash were checked. Instructor response placeholders were used only inside this temporary QA session, never in the student folder.

The 14-cell matrix was run headless. The six social trials verified the default visible viewer. No Lab 8 simulator remained after cleanup. The app uses the noninteractive Matplotlib backend rather than Qt plotting threads. Runtime records, test implementations and temporary submissions are excluded from Git. Student-facing test progress is cleared before handoff.

## Context and force-visual follow-up

All 37 automated tests pass in the course container. New checks cover the exact context example, force-vector addition and zero/outside-influence cases, rendered teaching figures and old-map evidence rejection. The revised disconnected map has free endpoints in separate chambers. Reference BFS, DFS and A* exhaust it in 9 expansions each. Reference IDDFS exhausts it in 231 expansions, below the 2,500-expansion demonstration budget.

The context handoff, context grid example and two-configuration force comparison were rendered and visually inspected. The field figure and path refinement call a common force helper so their mathematics cannot silently diverge. This refactor preserves the existing field equations, numerical clamps and step rule. No new claim about live robot performance is made by these teaching checks.

## October 29 student-experience revision

All 32 tests pass in the course container, including five progressive activities, automatic external-editing starter creation, four simultaneous offline map panels, a retained trajectory checkpoint, slider-driven social previews, incomplete ZIP backups, cost-switch behavior, colored worlds and conservative result reuse. Python compile checks also pass.

Browser verification confirmed drawing a start cell changes the saved planning problem, Show plan produces a route, both social maps display complete or explicitly partial refinements, and navigation resets the main scroll container to 0. A repeated global JavaScript declaration was the scroll failure and is now isolated inside a function scope.

The ROS package builds. A visible protocol-4 Nav2 open-map trial completed successfully in about 35 simulated seconds at the 0.30 m/s cap. A constrained RRT social smoke batch recorded a baseline controller failure, a lifecycle startup error and an explicit strong-field oscillation. These were retained as failures, not counted as successful navigation. The full 14-cell benchmark and a complete two-planner social matrix have not been rerun for this revision. Do not infer navigation reliability from a single smoke success. Rerun environment-error cells with the matching-result reuse command.

Pure-Python regression additionally verifies that a modest potential field follows the constrained reference route without cutting inflated corners. Genuine field failures retain a valid partial preview and never execute that prefix as a complete route.

Instructor test submissions and previous default trial imports are archived under ignored runtime storage before handoff. The student workflow has one status-labelled ZIP download. See REVISION_CHECKLIST.md for the comment-by-comment implementation record.

Checked on October 26, 2026 using Python 3.12 on Windows and the course ROS 2 Jazzy container.

Result: all 19 automated tests pass on both platforms. The ROS workspace builds and its software preflight passes.

## October 27 guided-learning update

All 26 tests pass on Windows and in the course Docker environment. The extended suite includes all four progressive activities, endpoint controls, step/play/pause/final-result controls, weighted shortest-cost comparisons, footprint-dependent connectivity, IDDFS resource limits, individual student-code checks and the valid zero-move case. Reference search and visualization code does not replace the student implementations.

Rendered architecture, scenario and weighted-route diagrams were visually inspected. Tutorial tests use temporary submission folders. Instructor visual-review artifacts are stored separately in ignored runtime archives. No new ROS replanning or moving-human experiment was added. The earlier ROS integration results below remain development checks, not a newly repeated full robot experiment matrix.

## Automated coverage

- Every guide page renders, including a comparison page populated with trial data.
- Page selection and written answers survive revisiting and restarting the app.
- Canonical maps are connected, coordinate conversion is consistent, and generated ROS map pixels preserve physical wall geometry.
- Invalid paths, incomplete code, unreachable goals and hard worker timeouts remain distinct.
- RRT and PRM are seeded, repeatable and collision checked.
- Social clearance subtracts both radii and exposure integrates simulation timestamps.
- Completion checks reject empty evidence, stale source, mismatched controllers and unmatched social trials.
- Autosave recovery preserves damaged files. Export manifests hash saved files.
- ROS package metadata and entry points build successfully with colcon.
- The ROS software preflight passes, including the Smac planner and Regulated Pure Pursuit packages.

## Actual ROS integration cases

Development trials exercised external BFS paths on both open and constrained maps. Both completed through the shared Regulated Pure Pursuit controller.

The final named Nav2 baseline, Smac 2D cost-aware A*, completed the constrained map. Earlier NavFn trials exposed a long-route planning failure. NavFn is not the released baseline.

Social integration trials exercised a human-unaware BFS baseline and both potential-field presets, all with executed trajectories. They also exercised an RRT controller failure and two explicit field-local-minimum outcomes. Failed trials remain evidence rather than being replaced with fabricated successes.

These are implementation smoke tests, not a complete experimental result set. The full seven-planner, two-map student comparison and repeated-seed statistics have not been executed with completed student implementations. The distributed student functions intentionally remain implementation tasks. No real-robot safety claim is made.

Instructor trial artifacts are kept under ignored runtime storage, outside the guide's normal trial discovery folder. The default student submission starts empty.
