# Live vision missions implementation

1. Reuse the original Sheffield pillar layout and both track textures with attribution. Build modern Gazebo worlds with explicit local materials and no online model dependency.
2. Launch a camera-equipped TurtleBot3 with a bounded camera resolution, simulation clock, image bridge and explicit command message type. Provide one repeatable start/stop/reset workflow and live ROS preflight before Mission 2.
3. Share resolution-independent vision processing and controller logic between the ROS nodes and unit tests. Pillar search turns only, centers each selected color, holds and records it. Line following uses a floor ROI, proportional steering, bounded speed, explicit line-loss stop and finish detection.
4. Place an independent command watchdog between student control and the simulator. Stop on missing/stale frames, invalid data, process exit and command timeout.
5. Record settings, per-frame decisions, commands, outcomes and representative images automatically. Let the guide read and preserve completed or interrupted attempts from the shared repository without uploads. Require evidence and explanations, not perfect scores.
6. Keep the three-part static detector investigation as Mission 1. Add Mission 2 and Mission 3 pages with scenarios, explanatory figures, numbered terminal steps, parameter references, focused experiments and questions. Update final readiness/export and retain old answers and archived policy work.
7. Test processing and failure cases locally, build ROS packages, verify actual camera/guard messages, and exercise both worlds. Report any unverified outcome explicitly. Archive instructor test state and restart the guide at the beginning after changes.
