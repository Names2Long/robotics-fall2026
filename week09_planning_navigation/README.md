# Lab 8 (Week 9): Planning and Human-Aware Navigation

An individual lab connecting offline search, actual simulated robot navigation, and human-aware route refinement.

## Three missions

1. Implement BFS, DFS, IDDFS and A* in real Python. Evaluate a short diagnostic corridor, two canonical maps and an unreachable goal. Compare path length, optimality ratio, planning time, expanded nodes and peak frontier.
2. Execute paths from those four methods, provided seeded RRT and PRM, and Nav2 Smac 2D cost-aware A*. Use the same Regulated Pure Pursuit FollowPath controller on open and constrained maps. Compare recorded outcomes, simulation time, distance, goal error, path tracking and clearance. All 14 planner/map cells are required. Repeats are recommended, not mandatory.
3. Choose at least two planners and compare human-unaware paths with two potential-field configurations in matched trials. Analyze body-to-body clearance, personal-space exposure, nearby speed and navigation trade-offs. Known static simulated people are not a human detector.

There is one technical synthesis followed by the course's common individual reflection, limited to 300 words.

## Guided preparation

Before Mission 1, five progressive activities let students draw walls and place endpoints directly on a teaching grid, inspect legal neighbors in a separate activity, step or play through reference searches, compare weighted-cost routes, and choose a robot planning radius of 0, 0.18 or 0.30 m. Frontier cells, expanded cells, the current state and parent-chain route are shown explicitly. The weighted example changes its preferred route between entry costs 1.2 and 1.3. These controls do not change mission maps.

The app creates `student_submission/mission_1/planners.py` on first launch without overwriting existing code. Students edit it in their preferred editor, not in the guide. Guidance explains the implicit graph, SearchContext, queues, stacks, heaps and parent reconstruction. AI assistance is permitted with explanation and testing. Mission 2 adds a prediction and a retained trajectory checkpoint inspection to the robot comparison.

Mission 1 introduces ctx first as a problem packet, then as a Python SearchContext object. A handoff diagram and an actual legal-neighbor example distinguish supplied tools from the student's frontier and parent records. The unreachable test uses two small chambers divided by a solid wall, with both endpoints free. All four reference methods exhaust this test without hitting the demo budget. Old test-map results need reevaluation rather than being shown as current evidence.

Mission 3 shows attraction, repulsion and their vector sum for both slider configurations at the same example position. The arrows use the exact force helper called by path refinement. A dotted influence boundary and proposed next point distinguish force direction from step size and robot speed.

Mission 1 provides implementation milestones and six individually runnable debugging checks: start equals goal, empty grid, detour, occupied goal, disconnected goal and narrow passage. These use the student's saved Python functions. The existing full evaluation remains the mission completion check.

A navigation-system diagram identifies student and supplied components. Mission 3 includes conceptual illustrations of permanent obstructions, temporary crossings and occupied shared spaces. No additional tutorial answers, moving-person simulation, or global-replanning experiment is required. Teaching controls do not alter the fixed experiment maps or robot radius.

## Start the guide

From the repository root, use the course container launcher:

Windows PowerShell:

~~~powershell
.\scripts\ros_course.ps1 lab week09_planning_navigation
~~~

macOS or Linux:

~~~bash
bash scripts/ros_course.sh lab week09_planning_navigation
~~~

The guide opens at http://localhost:8501. The ROS desktop is described in [the course setup guide](../ROS_DOCKER_SETUP.md).

Mission 1 can also run without ROS using Python 3.12 or newer:

~~~bash
cd week09_planning_navigation
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
~~~

## Build and check robot tools

Run inside a terminal in the course ROS desktop. Keep the app and ROS tools on the same repository bind mount.

~~~bash
cd /workspace/week09_planning_navigation
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install
cd ..
bash scripts/course_preflight.sh
~~~

The software check verifies ROS, Gazebo and package availability. Each experiment separately waits for active Nav2 lifecycle nodes, map-frame transforms and lidar. Do not launch teleop or a second navigation stack beside a batch.

## Robot trials

~~~bash
# Inspect one run first. The GUI is optional.
bash scripts/run_trials.sh --mission 2 --planners nav2 --maps open
# Full two-map comparison, one attempt per planner/map cell.
bash scripts/run_trials.sh --mission 2 --skip-existing
# Optional repeats use seeds 0, 1 and 2.
bash scripts/run_trials.sh --mission 2 --repeats 3
# After saving field configurations in the Mission 3 page:
bash scripts/run_trials.sh --mission 3 --planners astar rrt --maps open --skip-existing --fields student_submission/mission_3/potential_fields.json
~~~

The wrapper uses ROS_DOMAIN_ID=29. Each attempt gets a private Gazebo transport partition, recorded in request.json and shared by that attempt's server and viewer. It restarts the complete simulation and Nav2 for every attempt and terminates remaining child processes after the launcher exits. Gazebo is visible by default, with a light floor, blue exterior walls, brown internal obstacles and orange people. Use `--headless` to opt out of the viewer. Terminal messages identify the current trial, remaining count and startup or execution phase. The default execution deadline is 180 simulated seconds. `--skip-existing` reuses outcomes only when protocol, map, source, field settings and deadline match. Environment errors are never reused. Existing attempts are never overwritten. Use Ctrl+C to interrupt a batch.

The guide discovers shared files directly. It selects the latest attempt for each experimental cell and copies selected evidence into the submission when the mission is saved. A planner failure is evidence. An environment failure is a setup problem to fix. IDDFS can reach its search budget on a large map. This is not evidence that no route exists.

## Evidence and interpretation

- Four-connected grid edges cost one and represent 0.25 m. All offline methods use identical conservative obstacle inflation.
- RRT and PRM edges are collision checked on that same inflated map. PRM builds an undirected nearest-neighbour roadmap and uses Dijkstra search.
- Nav2 uses [Smac 2D cost-aware A* with built-in smoothing](https://ros-navigation.github.io/mkdocs.nav2.org/jazzy/configuration_and_development/configuration_guide/planners_plugins/smac/smac_2d/configuring_smac_2d/). It is a named system baseline, not an identical binary-grid implementation.
- The ROS map subdivides each 0.25 m teaching cell into 5 by 5 cells at 0.05 m resolution without changing wall geometry.
- External and Nav2 paths use one FollowPath controller and common maximum forward speed of 0.30 m/s, including the downstream velocity smoother. Routes are uniformly resampled before execution. The common PositionGoalChecker uses a 0.25 m position tolerance. No final parking orientation is specified by this task. Protocol version 7 prevents mixing earlier controller and simulator-isolation configurations with this experiment.
- Experiments start localization plus the planner, controller, velocity smoother and collision monitor. Unused docking, route, waypoint and behavior-tree servers are not part of these fixed-path trials. The runner waits for all four managed navigation nodes to be active before requesting motion.
- Offline planning uses a wall-clock timer. Nav2 reports its internal planning duration, with action round-trip time recorded separately. Robot execution uses simulation time. Successful path generation is separate from successful execution.
- Recorded poses are AMCL map-frame estimates, not simulator ground truth. Static clearance uses those estimates and cell geometry. Lidar range is a proximity proxy, not a measured collision count.
- Human clearance subtracts robot and person radii. Personal-space exposure uses elapsed simulation time. The 0.75 m threshold is a scenario choice, not a universal comfort standard.
- Potential fields can have local minima and oscillations. Failed refinement is recorded, not silently replaced with a successful baseline.
- Mission 3 sliders update open and constrained previews side by side. A failed refinement shows its valid prefix as a dashed line, not a complete route. Save chosen settings before running paired trials. Failed prefixes are never executed.

## Submission and recovery

Use Save and prepare ZIP on the last page, then Download submission ZIP. The single archive is marked complete only when all checks pass. Otherwise it is an incomplete backup. Inspect student_submission and commit that folder. Normal submission files are visible to Git. Runtime, virtual environments and ROS build outputs are ignored. Autosaves preserve readable backups. Final manifests hash each exported file.

Use WEEK09_SUBMISSION_DIR to isolate instructor tests. Do not reset student work when updating the repository. Earlier scaffold evidence is preserved as responses but does not automatically complete revised missions.

## Maintainer verification

~~~bash
python -m unittest discover -s tests -v
python -m compileall -q app.py lab planning scripts ros2_ws/src/week09_nav_tools
~~~

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for implementation groups and [content/instructor_notes.md](content/instructor_notes.md) for release checks. Old plan_probe, navigate_probe, social_monitor and their old contract tests are retained as legacy tools. The new guide uses experiment_probe and evaluation/experiments.py, not the earlier five-goal or costmap-fragment assignments.
