# Week 6 Lab Overview: SLAM and Mapping

This individual ROS 2 lab connects motion estimates, LiDAR evidence, and occupancy-grid mapping. Students use SLAM Toolbox in TurtleBot3 House. They do not implement scan matching. The shared course container supplies ROS 2 Jazzy, Gazebo, TurtleBot3, and RViz.

Three guided tutorials prepare two mapping runs. Tutorial 1 revisits encoders, dead reckoning, and accumulated odometry error from Lab 4. Tutorial 2 contrasts topological and metric maps and lets students explore how LiDAR rays update an occupancy grid. After preflight, Tutorial 3 teaches students to distinguish a live scan, an estimated pose, and accumulated map evidence in RViz.

Mission 1 asks students to predict a route, teleoperate the robot, revisit a mapped region, and save a checked YAML/PGM/analysis bundle plus RViz evidence. They interpret unknown space, visible structure, and possible effects of motion error. The composite map score is a discussion aid, not a passing threshold.

Mission 2 changes the exploration route while keeping the world and robot start the same. Students record elapsed time, save a second map, and compare the two maps using quantitative and visual evidence. No minimum coverage, resolution, or quality score is required to pass either mission. Students must still produce matching, readable map files and explain their observations.

The final technical synthesis uses both mapping runs to explain what the robot can and cannot infer about the environment. A separate individual reflection completes the submission. The submission includes checked artifacts and a hashed manifest. Recoverable autosaves, explicit navigation, and a ZIP backup protect work across restarts and updates.

The former AMCL localization tutorials and Mission 3 are preserved in [the future-lab localization module](../future_lab_modules/localization_from_saved_map/README.md). They are not part of the active Lab 6 flow or submission.
