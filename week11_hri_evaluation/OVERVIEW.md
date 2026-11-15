# Lab 10 · Voice, Shared Control, and Assistive Handover

This individual ROS 2 lab investigates how a robot should understand a spoken goal, ask for permission, respond to a correction, and wait for a person at the end of a delivery.

Four illustrated activities explain the speech pipeline, handover readiness, a Python interaction rule, and control authority. Students edit code inside the guide and inspect the effect of each event before beginning robot trials.

In Mission 1 students complete and check their interaction controller, then test it on a TurtleBot3 in a Gazebo cup delivery room. In Mission 2 they speak a clear request, an ambiguous request, a correction, and a cancellation. They inspect transcripts, controller decisions, and robot poses, then improve one feedback message and retest it. In Mission 3 they compare manual teleoperation, voice shared autonomy, and supplied autonomous execution on normal and changed-goal deliveries.

Robot movement is executed through ROS velocity commands and measured through Gazebo odometry. Cup loading and transfer use a simulated tray state. The person must authorize the final handover. The final synthesis uses the recorded trials to explain how interaction design changes the work shared between person and robot.
