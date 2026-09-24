# Week 4 Lab Overview: PID Control and Odometry

This individual, self-contained Streamlit lab helps students connect feedback control, measurement, and responsible robot motion. ROS 2 is not required, allowing students to focus on controller behavior and odometry rather than middleware setup.

The guided walkthrough begins with a familiar stopping problem, contrasts open-loop and feedback control, and demonstrates how proportional, integral, and derivative terms affect response. It then introduces tracking wheels, encoders, wheel circumference, heading geometry, and accumulated pose estimation. Each transition explains how the simplified visualization relates to the more complex robot used in the missions.

Mission 1 applies PID concepts to a two-link robot arm. Students predict the effects of insufficient proportional and derivative action, tune shoulder and elbow controllers, use gravity compensation, hold three target poses, and compare measured behavior with their prediction.

Mission 2 extends odometry to a holonomic robot. Students predict how incorrect forward and sideways pod scales affect the pose estimate, calibrate both pod scales, and run a multi-direction test. The independently checked requirement is a maximum error below 3.0 inches.

Mission 3 combines planning, PID control, odometry, and human-centered evaluation. Students draw a route or enter route coordinates, visit four waypoints in order, preserve pedestrian clearance, and meet mean and maximum tracking-error limits. Their analysis connects technical evidence with a concrete safety margin, performance trade-off, and responsibility for verification.

The guide autosaves responses and mission state and restores compatible work after a restart. Mission passes become stale when relevant results change. The final save is unavailable until all three missions, required responses, student identity, evidence, and the reflection are complete. Students commit the generated `student_submission/` folder and submit the URL of the individual Git commit.
