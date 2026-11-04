# Lab 8 implementation

1. Shared experiment core
   - Canonical open and constrained maps, common units and collision checking.
   - Student Python implementations of BFS, DFS, IDDFS and A*.
   - Bounded offline evaluation, path validation and standard search metrics.
   - Supplied seeded RRT and PRM with collision-checked edges.
2. Robot experiments
   - Generate matching simulation worlds and occupancy maps.
   - Run Nav2 and external paths through the same FollowPath controller.
   - Restart the simulation between trials and record failures as well as successes.
   - Compare seven planners on both maps using navigation metrics.
3. Social navigation
   - Add known simulated people and a common potential-field refinement.
   - Compare human-unaware paths and two social configurations for two planners.
   - Report personal-space exposure, clearance, time, distance and failures.
4. Student workflow
   - Explain concepts before commands and measurements before questions.
   - Bottom back/next navigation, local evidence discovery and resumable work.
   - One technical synthesis and the shared individual reflection.
5. Saving and release checks
   - Atomic autosave with recovery, source and configuration hashes, export manifest.
   - Submission files remain visible to Git.
   - Unit tests, app smoke tests and ROS integration checks.

Instructor testing data belongs in runtime, not in the default submission folder.
Do not clear student work when updating or launching the lab.

## Implemented groups

- [x] Shared core, editable student source and bounded offline workers.
- [x] Matched maps/worlds, seeded RRT/PRM and common-controller robot trials.
- [x] Potential-field refinement and social metrics with explicit failure outcomes.
- [x] Revised guide, footer navigation, local evidence discovery and shared reflection.
- [x] Recoverable saving, CSV/figure evidence, source snapshots and hashed exports.
- [x] Automated tests, ROS build/preflight and representative integration trials.

See RELEASE_TESTING.md for the scope and limits of the actual verification. The complete student experiment matrix is not represented as already tested.

## Guided-learning additions, October 27

- [x] Editable teaching grid, movable endpoints and legal-neighbor inspection.
- [x] Step/play BFS, DFS, IDDFS and A* traces with frontier and exploration views.
- [x] Supplied BFS, Dijkstra and A* comparison on weighted terrain.
- [x] Side-by-side point and body-radius planning with adjustable inflation.
- [x] Six implementation milestones and six individually runnable student-code checks.
- [x] Navigation-system diagram identifying student and supplied components.
- [x] Illustrated permanent-obstruction, temporary-crossing and shared-space explanations.
- [x] No replanning experiment or additional written tutorial requirements.
