# Lab 8 student-experience revision, October 29

## Playground

- [x] Activity 1 has an explicit create, predict, plan, revise task.
- [x] Remove the mission-conventions expander from the playground.
- [x] Draw and erase walls, place start and goal on the grid, then press Show plan.
- [x] Explain legal neighbors in their own activity. There are now five activities.
- [x] Weighted-cost control includes a real route switch between 1.2 and 1.3.
- [x] Robot-radius control has only 0, 0.18 and 0.30 m.

## Mission 1

- [x] Create the starter file at app launch and edit it externally. Never overwrite existing code.
- [x] State permitted AI assistance and the student's explanation and testing responsibilities.
- [x] Separate implementation guidance into numbered sections.
- [x] Explain ctx, implicit graph vertices and edges, imports, queues, stacks, heaps and helpers.
- [x] Ask direct questions using named rows and columns, including why BFS and A* lengths agree.
- [x] Show all four test maps with returned paths without a map dropdown.

## Mission 2

- [x] Explain that the existing environment check completes setup, with no new manual launch.
- [x] Explain the seven planners, controller, matched conditions and navigation metrics.
- [x] Color the Gazebo floor, walls, obstacles and people with lighting.
- [x] Launch the GUI by default, add headless opt-out, current/total counts and progress heartbeat.
- [x] Raise the common speed cap to 0.30 m/s, including the velocity smoother.
- [x] Use a 180 simulated-second deadline and skip unchanged matching attempts on request.
- [x] Explain shortest-path equality for BFS and A*.
- [x] Separate open and constrained metric charts.
- [x] Add a prediction and interactive trajectory checkpoint investigation, retained as evidence.

## Mission 3 and submission

- [x] Remove the instructor-facing illustration disclaimer.
- [x] Explain the delivery scenario, potential-field forces, every equation term and the task.
- [x] Replace JSON editing with sliders and side-by-side map previews.
- [x] Show failed social refinements as explicitly labelled partial paths instead of hiding them.
- [x] Correct premature waypoint switching that cut constrained-map corners and caused artificial field failures.
- [x] Ask how parameter changes affected the preview paths.
- [x] Ask results-table questions with named metrics and explicit comparison instructions.
- [x] Apply the same speed, progress and matching-result reuse improvements to social trials.
- [x] Fix repeated page scroll-reset declarations and cover activity navigation as well as pages.
- [x] Replace separate complete/draft downloads with one status-labelled ZIP workflow.

## Verification scope

Automated tests exercise all pages, progressive controls, external source checks, field settings, incomplete backups, cost thresholds, world geometry and materials. Preliminary smoke tests are not substitutes for the full release acceptance recorded below. Commit reviewed source only, never instructor runtime records or student submissions.

## Follow-up: context and force explanations

- [x] Explain ctx with a problem-packet analogy before introducing the Python object interface.
- [x] Show the runner-to-context-to-function handoff and a concrete legal-neighbor example.
- [x] Explain what belongs to ctx and what the student must store and decide independently.
- [x] Replace the occupied-goal case with two free chambers disconnected by a solid wall.
- [x] Verify all four reference searches return no_path without reaching the demo budget.
- [x] Reject old offline map fingerprints until the student reevaluates the revised cases.
- [x] Visualize attraction, repulsion, their vector sum and the proposed step for both live social configurations.
- [x] Use the same force computation for the figure and actual path refinement.

The follow-up suite has 37 passing tests. Teaching figures are rendered and visually inspected. No ROS behavior experiment was needed for the explanation update, and robot-trial map geometry is unchanged.

## Release hardening and acceptance

- [x] Launch only required Nav2 lifecycle services and wait for the controller, planner, smoother and collision monitor.
- [x] Use one position-only goal checker for the destination task.
- [x] Isolate every simulator with a unique transport partition.
- [x] Kill remaining launcher-group descendants and regression-test an exited parent with a live child.
- [x] Execute current planner source bytes instead of reusing timestamp-based Python caches.
- [x] Keep interpreter caches out of submission ZIPs and use noninteractive web plotting.
- [x] Run all 14 isolated navigation cases and accept only valid experiment outcomes.
- [x] Run six visible paired social cases for two planners.
- [x] Verify measured evidence through final app readiness and complete ZIP hashes in a temporary QA folder.

The final suite has 42 passing tests. Detailed release evidence and bounded-failure outcomes are recorded in RELEASE_TESTING.md.
