# Mission 1

## Scan Observation

I noticed that the range min was 0.11 while the range max was 3.5 which repersents the robots distances 

## Guided Checks

{'node_list': True, 'guard_info': True, 'bridge_info': True, 'scan_info': True, 'scan_message': True, 'command_topics': True}

## Graph Explanation

A ROS 2 graph shows which programs are running and how they messages each other. I noticed the node /ros_gz_bridge publishes the LiDAR distance readings onto topic and scan, along with the /course_evidence_collector subscribes to that same topic to receive them. 

## Command Path Explanation

A proposed command travels on /student_cmd_vel as a Twist message. The guard node /course_cmd_vel_guard subscribes to it, and checks whether the requested motion is within its safe limits, and only then publishes an approved TwistStamped message onto /cmd_vel. 

## Tools Explanation

Gazebo is responsible for simulating the physics of the virtual world. Since it computes wheel motion, collisions with walls, and the LiDAR readings themselves. While RViz is responsible only for displaying data that already exists, so a person can see the scan and the robots pose. Overall Gazebo creates the data while RViz receives the data.
